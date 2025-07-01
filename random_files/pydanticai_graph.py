from __future__ import annotations
import secrets
import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
import logfire
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ------------------------- Configuration -------------------------
# logfire.configure()
# logfire.instrument_pydantic_ai()

LOCAL_PROVIDER = OpenAIProvider(base_url="http://localhost:11434/v1")
DEFAULT_MODEL_ID = "ollama/qwen3:4b"
MODEL_NAME = DEFAULT_MODEL_ID.split("ollama/")[1]
LOCAL_MODEL = OpenAIModel(model_name=MODEL_NAME, provider=LOCAL_PROVIDER)

# ------------------------ Pydantic Models ------------------------
class ResumeInput(BaseModel):
    resume_text: str = Field(..., min_length=10)
    job_description: str = Field(..., min_length=10)

class ContextSummary(BaseModel):
    summary: str
    matching_skills: list[str]
    experience_level: str
    recommended_difficulty: str

class TailoredQuestion(BaseModel):
    question: str
    ideal_answer: str
    tags: list[str]
    difficulty: str

class InterviewTurn(BaseModel):
    question: str
    ideal_answer: str
    candidate_answer: str
    timestamp: datetime = Field(default_factory=datetime.now)
    response_time_seconds: float

class Evaluation(BaseModel):
    score: int
    feedback: str
    strengths: list[str]
    improvements: list[str]

class FinalReport(BaseModel):
    session_id: str
    turns: list[InterviewTurn]
    evaluations: list[Evaluation]
    overall_score: float
    technical_score: float
    communication_score: float
    duration: str

# ------------------------ Classification ------------------------

class ResponseType(str, Enum):
    answer = 'answer'
    clarification = 'clarification'
    unrelated = 'unrelated'

class ClassificationOutput(BaseModel):
    classification: ResponseType
    explanation: str

# ------------------------ Agent Definitions ------------------------
context_agent = Agent(
    LOCAL_MODEL,
    deps_type=ResumeInput,
    output_type=ContextSummary,
    system_prompt=(
        "You are an expert technical recruiter. Analyze the candidate's resume and job description. "
        "Provide a concise summary of their background, matching skills, experience level, and recommended difficulty."
    )
)

question_generation_agent = Agent(
    LOCAL_MODEL,
    deps_type=str,
    output_type=list[TailoredQuestion],
    system_prompt=(
        "You are an expert interviewer. Given a job description, generate 5 tailored interview questions with ideal answers, tags, and difficulty."
    )
)

evaluation_agent = Agent(
    LOCAL_MODEL,
    deps_type=InterviewTurn,
    output_type=Evaluation,
    system_prompt=(
        "You are an expert evaluator. Given the question, ideal answer, and candidate answer, "
        "score out of 100 and provide feedback, strengths, and improvements."
    )
)

classification_agent = Agent(
    LOCAL_MODEL,
    output_type=ClassificationOutput,
    system_prompt=(
        "You are an assistant that classifies a candidate's response into one of three categories: "
        "'answer' (they attempted to answer the question), "
        "'clarification' (they are asking for more details or clarification), "
        "or 'unrelated' (their response is off-topic). "
        "Respond with the JSON fields 'classification' and 'explanation'. "
        "If classification is 'answer', the explanation can be brief (e.g. 'Looks like an answer'). "
        "If 'clarification', the explanation should restate the question in simpler terms. "
        "If 'unrelated', politely remind them to focus on the question."
    )
)

# ------------------------ Graph State ------------------------
@dataclass
class InterviewState:
    resume: str
    job: str
    context: ContextSummary | None = None
    questions: list[TailoredQuestion] = field(default_factory=list)
    turns: list[InterviewTurn] = field(default_factory=list)
    evaluations: list[Evaluation] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    current_index: int = 0
    session_id: str = field(default_factory=lambda: secrets.token_hex(8))

# ------------------------ Graph Nodes ------------------------
@dataclass
class AnalyzeContext(BaseNode[InterviewState, None, InterviewState]):
    async def run(self, ctx: GraphRunContext[InterviewState]) -> SelectQuestions:
        logger.info("🔍 Analyzing candidate resume and job requirements...")
        inp = ResumeInput(resume_text=ctx.state.resume, job_description=ctx.state.job)
        result = await context_agent.run(
            f"Resume: {ctx.state.resume}\n\nJob Description: {ctx.state.job}",
            deps=inp
        )
        ctx.state.context = result.output
        logger.info(f"✅ Context analysis complete: {ctx.state.context.summary[:100]}...")
        logger.info(f"📊 Experience level: {ctx.state.context.experience_level}")
        logger.info(f"🎯 Recommended difficulty: {ctx.state.context.recommended_difficulty}")
        return SelectQuestions()

@dataclass
class SelectQuestions(BaseNode[InterviewState, None, InterviewState]):
    async def run(self, ctx: GraphRunContext[InterviewState]) -> PrepareInterview:
        logger.info("❓ Generating tailored interview questions...")
        result = await question_generation_agent.run(
            f"Generate 5 tailored interview questions for this job: {ctx.state.job}",
            deps=ctx.state.job
        )
        ctx.state.questions = result.output
        logger.info(f"✅ Generated {len(ctx.state.questions)} questions:")
        for i, q in enumerate(ctx.state.questions, 1):
            logger.info(f"   Q{i}: {q.question}")
            logger.info(f"       Difficulty: {q.difficulty}")
        return PrepareInterview()

@dataclass
class PrepareInterview(BaseNode[InterviewState, None, InterviewState]):
    async def run(self, ctx: GraphRunContext[InterviewState]) -> End[InterviewState]:
        # This node just prepares the interview state and ends
        # The actual interview will be handled via WebSocket
        logger.info("🎯 Interview preparation complete - ready for candidate!")
        return End(ctx.state)

# ------------------------ Build Graph ------------------------
interview_graph = Graph(
    nodes=[AnalyzeContext, SelectQuestions, PrepareInterview]
)

# ------------------------ FastAPI App ------------------------
app = FastAPI()
sessions: dict[str, InterviewState] = {}

# Serve HTML interface
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Interview Bot</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f4f4; }
    #chat { max-width: 800px; margin: 40px auto; background: #fff; padding: 20px; border-radius: 8px; height: 500px; overflow-y: auto; }
    .message { margin: 10px 0; }
    .bot { color: #333; }
    .user { text-align: right; color: #0066cc; }
    #input { width: calc(100% - 100px); padding: 10px; }
    #send { width: 80px; padding: 10px; }
  </style>
</head>
<body>
  <div id="chat"></div>
  <div style="max-width:800px;margin:0 auto;display:flex;gap:10px;">
    <input id="input" placeholder="Type your answer..." />
    <button id="send">Send</button>
  </div>
<script>
  let ws;
  window.onload = async () => {
    // Default resume and job description (programmatically set)
    const resume_text = 'AI Engineer';
    const job_description = 'ai ENGINEEr';
    
    // Create session
    const res = await fetch('/session', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resume_text,job_description})});
    const data = await res.json();
    ws = new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/${data.session_id}`);
    ws.onmessage = e => {
      const msg = JSON.parse(e.data);
      const div = document.createElement('div');
      div.className = 'message bot';
      if (msg.question) {
        div.textContent = `Question: ${msg.question}`;
      } else if (msg.evaluation) {
        div.innerHTML = `<strong>Score:</strong> ${msg.evaluation.score}/100<br/><strong>Feedback:</strong> ${msg.evaluation.feedback}`;
      } else if (msg.clarification) {
        div.innerHTML = `<em>Clarification:</em> ${msg.clarification}`;
      } else if (msg.warning) {
        div.innerHTML = `<em>Warning:</em> ${msg.warning}`;
      } else if (msg.feedback) {
        div.innerHTML = `<strong>Context Summary:</strong> ${msg.feedback}`;
      } else if (msg.summary) {
        div.innerHTML = `<strong>Final Report:</strong><br/>Overall Score: ${msg.summary.overall_score}/100<br/>Duration: ${msg.summary.duration}`;
      }
      document.getElementById('chat').append(div);
      document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
    };
  };
  const send_message = () => {
    const txt = document.getElementById('input').value.trim();
    if (!txt) return;
    ws.send(txt);
    const div = document.createElement('div'); div.className='message user'; div.textContent=txt;
    document.getElementById('chat').append(div);
    document.getElementById('input').value='';
    document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
  };
  
  document.getElementById('send').onclick = send_message;
  document.getElementById('input').onkeypress = e => {
    if (e.key === 'Enter') send_message();
  };
</script>
</body>
</html>
"""

@app.get('/', response_class=HTMLResponse)
async def home():
    return HTML_INTERFACE

@app.post('/session')
async def create_session(req: ResumeInput):
    # Create initial state and run context analysis and question generation using the graph
    state = InterviewState(resume=req.resume_text, job=req.job_description)
    logger.info("🚀 Starting new interview session")
    logger.info(f"📄 Resume: {len(req.resume_text)} characters")
    logger.info(f"💼 Job description: {len(req.job_description)} characters")
    
    # Run the graph to analyze context and generate questions
    result = await interview_graph.run(AnalyzeContext(), state=state)
    final_state = result.output
    
    sessions[final_state.session_id] = final_state
    logger.info("✅ Interview session initialized - waiting for candidate connection")
    return {'session_id': final_state.session_id}

@app.websocket('/ws/{session_id}')
async def ws_endpoint(websocket: WebSocket, session_id: str):
    if session_id not in sessions:
        logger.warning("❌ WebSocket connection attempted for unknown session")
        await websocket.close(code=4404)
        return
    
    await websocket.accept()
    state = sessions[session_id]
    logger.info("🔌 Candidate connected - starting interview!")
    
    # Send context summary
    logger.info("📤 Sending interview context to candidate")
    await websocket.send_json({'feedback': state.context.summary})
    try:
        for i, q in enumerate(state.questions, 1):
            # Send question
            logger.info(f"❓ Question {i}/{len(state.questions)}: {q.question}")
            await websocket.send_json({'question': q.question})
            question_start_time = datetime.now()

            while True:
                # Wait for candidate response
                logger.info("⏳ Waiting for candidate's response...")
                ans = await websocket.receive_text()
                response_end_time = datetime.now()
                logger.info(f"💬 Candidate said: '{ans}'")

                # Classify response
                class_res = await classification_agent.run(
                    f"Question: {q.question}\nResponse: {ans}"
                )
                cls = class_res.output.classification
                explanation = class_res.output.explanation

                if cls == ResponseType.answer:
                    response_time = (response_end_time - question_start_time).total_seconds()
                    turn = InterviewTurn(
                        question=q.question, ideal_answer=q.ideal_answer,
                        candidate_answer=ans, response_time_seconds=response_time
                    )
                    logger.info("🔍 Evaluating candidate's answer...")
                    res = await evaluation_agent.run(
                        f"Evaluate this interview response:\nQuestion: {turn.question}\nIdeal Answer: {turn.ideal_answer}\nCandidate Answer: {turn.candidate_answer}",
                        deps=turn
                    )
                    state.turns.append(turn)
                    state.evaluations.append(res.output)
                    logger.info(f"📊 Score: {res.output.score}/100 | {res.output.feedback[:80]}...")
                    await websocket.send_json({'evaluation': res.output.model_dump(mode="json")})
                    break  # move to next question

                elif cls == ResponseType.clarification:
                    logger.info("🛈 Candidate asks for clarification. Sending explanation...")
                    await websocket.send_json({'clarification': explanation})
                    # loop continues waiting for answer

                else:  # unrelated
                    logger.info("⚠️ Candidate response unrelated. Sending reminder...")
                    await websocket.send_json({'warning': explanation})
                    # loop continues waiting for answer
                    
        # Generate final report
        logger.info("📊 Interview complete! Generating final report...")
        # compute scores
        overall = sum(e.score for e in state.evaluations)/len(state.evaluations)
        tech = sum(e.score for e in state.evaluations)/len(state.evaluations)
        report = FinalReport(
            session_id=state.session_id, turns=state.turns,
            evaluations=state.evaluations, overall_score=overall,
            technical_score=tech, communication_score=tech,
            duration=str(datetime.now()-state.start_time)
        )
        
        # Save
        Path('reports').mkdir(exist_ok=True)
        report_path = f'reports/{state.session_id}.json'
        with open(report_path, 'w') as f:
            json.dump(report.model_dump(mode="json"), f, indent=2)
        logger.info(f"💾 Report saved to {report_path}")
        logger.info(f"🎯 FINAL SCORE: {overall:.1f}/100")
        logger.info(f"⏱️  Interview duration: {report.duration}")
        
        await websocket.send_json({'summary': report.model_dump(mode="json")})
        logger.info("🎉 Interview session completed successfully!")
        await websocket.close()
    except WebSocketDisconnect:
        logger.info("🔌 Candidate disconnected from interview")
        pass

@app.get('/session/{session_id}/report')
async def get_report(session_id: str):
    path = Path('reports')/f'{session_id}.json'
    if not path.exists(): raise HTTPException(404)
    return path.read_text()

if __name__ == '__main__':
    logger.info("🚀 Starting AI Interview Bot server...")
    logger.info(f"🤖 Using model: {MODEL_NAME}")
    logger.info("🌐 Server will be available at http://0.0.0.0:8065")
    uvicorn.run(app, host='0.0.0.0', port=8065)
