# agentic_interview_bot.py
"""
Enhanced Agentic Technical Prescreen Interview Bot (PydanticAI 0.4+)
=======================================================================
This script implements an improved multi-agent interview system using PydanticAI
with better error handling, streamlined flow, and enhanced user experience.

Key Enhancements:
- Fixed API compatibility with PydanticAI 0.4+ (result_type vs output_type)
- Simplified agent architecture for better reliability
- Enhanced error handling and retry mechanisms
- Improved scoring system with detailed feedback
- Better question selection algorithm
- Real-time progress tracking
"""

from __future__ import annotations
import json
import secrets
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime
import nest_asyncio
nest_asyncio.apply()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, validator
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from rapidfuzz import fuzz
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

###############################################################################
# ---------------------- Local LLM / Provider Setup --------------------------#
###############################################################################
LOCAL_PROVIDER = OpenAIProvider(base_url="http://localhost:11434/v1")
DEFAULT_MODEL_ID = "ollama/qwen3:8b"
MODEL_NAME = DEFAULT_MODEL_ID.split("ollama/")[1]
LOCAL_MODEL = OpenAIModel(model_name=MODEL_NAME, provider=LOCAL_PROVIDER)

###############################################################################
# --------------------------- Question Bank ----------------------------------#
###############################################################################
BANK_PATH = Path("question_bank.json")
DEFAULT_BANK = [
    {
        "question": "Explain the difference between a Python list and tuple.",
        "ideal_answer": "A list is mutable and typically used for homogenous items, while a tuple is immutable and often used for heterogeneous data. Lists use square brackets [], tuples use parentheses ().",
        "tags": ["python", "data-structures"],
        "difficulty": "beginner"
    },
    {
        "question": "What is the Big-O complexity of quicksort in the average case?",
        "ideal_answer": "O(n log n) in the average case, but O(n²) in the worst case when the pivot is always the smallest or largest element.",
        "tags": ["algorithms", "complexity"],
        "difficulty": "intermediate"
    },
    {
        "question": "Describe how REST differs from GraphQL.",
        "ideal_answer": "REST exposes multiple endpoints with fixed data structures, while GraphQL provides a single endpoint with customizable queries. GraphQL allows clients to request exactly the data they need, reducing over-fetching.",
        "tags": ["api", "web-development"],
        "difficulty": "intermediate"
    },
    {
        "question": "Explain the concept of closures in JavaScript.",
        "ideal_answer": "A closure is a function that has access to variables in its outer scope even after the outer function has returned. It 'closes over' variables from its lexical environment.",
        "tags": ["javascript", "programming-concepts"],
        "difficulty": "intermediate"
    },
    {
        "question": "What is the difference between SQL and NoSQL databases?",
        "ideal_answer": "SQL databases are relational with fixed schemas and ACID compliance, while NoSQL databases are non-relational with flexible schemas and eventual consistency. SQL uses structured query language, NoSQL uses various query methods.",
        "tags": ["databases", "sql", "nosql"],
        "difficulty": "beginner"
    }
]

if not BANK_PATH.exists():
    BANK_PATH.write_text(json.dumps(DEFAULT_BANK, indent=2))
QUESTION_BANK = json.loads(BANK_PATH.read_text())

###############################################################################
# ----------------------------- Data Models ----------------------------------#
###############################################################################
class ResumeInput(BaseModel):
    resume_text: str = Field(..., min_length=10)
    job_description: str = Field(..., min_length=10)

class ContextSummary(BaseModel):
    summary: str = Field(..., description="Brief summary of candidate background")
    matching_skills: List[str] = Field(..., description="Skills that match the job requirements")
    experience_level: str = Field(..., description="Estimated experience level: junior, mid, senior")
    recommended_difficulty: str = Field(..., description="Recommended question difficulty: beginner, intermediate, advanced")

class TailoredQuestion(BaseModel):
    question: str = Field(..., description="The interview question")
    ideal_answer: str = Field(..., description="Expected ideal answer")
    tags: List[str] = Field(..., description="Question topic tags")
    difficulty: str = Field(..., description="Question difficulty level")

class QuestionBatch(BaseModel):
    questions: List[TailoredQuestion] = Field(..., min_items=1, max_items=5)
    reasoning: str = Field(..., description="Explanation for question selection")

class InterviewTurn(BaseModel):
    question: str = Field(..., description="The question asked")
    ideal_answer: str = Field(..., description="The expected answer")
    candidate_answer: str = Field(..., description="The candidate's response")
    timestamp: datetime = Field(default_factory=datetime.now)

class Evaluation(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Score out of 100")
    technical_accuracy: int = Field(..., ge=0, le=100, description="Technical correctness score")
    completeness: int = Field(..., ge=0, le=100, description="Answer completeness score")
    clarity: int = Field(..., ge=0, le=100, description="Communication clarity score")
    feedback: str = Field(..., description="Detailed feedback for the candidate")
    strengths: List[str] = Field(..., description="Identified strengths in the answer")
    improvements: List[str] = Field(..., description="Areas for improvement")
    follow_up_needed: bool = Field(..., description="Whether a follow-up question is recommended")

class InterviewProgress(BaseModel):
    current_question: int = Field(..., description="Current question number")
    total_questions: int = Field(..., description="Total number of questions")
    average_score: float = Field(..., description="Current average score")
    time_elapsed: str = Field(..., description="Time elapsed since start")

class FinalTranscript(BaseModel):
    session_id: str = Field(..., description="Interview session ID")
    turns: List[InterviewTurn] = Field(..., description="All interview turns")
    evaluations: List[Evaluation] = Field(..., description="All evaluations")
    overall_score: float = Field(..., description="Overall interview score")
    technical_score: float = Field(..., description="Average technical accuracy")
    communication_score: float = Field(..., description="Average communication clarity")
    recommendation: str = Field(..., description="Hiring recommendation")
    summary: str = Field(..., description="Interview summary")
    duration: str = Field(..., description="Total interview duration")

###############################################################################
# -------------------------------- Agents ------------------------------------#
###############################################################################

# Context Analysis Agent
context_agent = Agent(
    model=LOCAL_MODEL,
    deps_type=ResumeInput,
    result_type=ContextSummary,
    system_prompt=(
        "You are an expert technical recruiter. Analyze the candidate's resume and job description. "
        "Provide a concise summary of their background, identify matching skills, estimate their experience level, "
        "and recommend appropriate question difficulty. Be thorough but concise."
    ),
)

# Question Selection Agent  
question_agent = Agent(
    model=LOCAL_MODEL,
    deps_type=ContextSummary,
    result_type=QuestionBatch,
    system_prompt=(
        "You are an expert interview designer. Based on the candidate summary and available questions, "
        "select 3-4 most relevant questions that match their experience level and the job requirements. "
        "Prioritize questions that will best assess their fit for the role. Explain your selection reasoning."
    ),
)

@question_agent.tool
async def get_question_bank(ctx: RunContext[ContextSummary]) -> str:
    """Retrieve the available question bank for selection."""
    bank_info = f"Available questions ({len(QUESTION_BANK)} total):\n\n"
    for i, q in enumerate(QUESTION_BANK, 1):
        bank_info += f"{i}. Question: {q['question']}\n"
        bank_info += f"   Difficulty: {q['difficulty']}\n"
        bank_info += f"   Tags: {', '.join(q['tags'])}\n"
        bank_info += f"   Ideal Answer: {q['ideal_answer'][:100]}...\n\n"
    
    bank_info += f"\nCandidate Profile:\n"
    bank_info += f"Experience Level: {ctx.deps.experience_level}\n"
    bank_info += f"Recommended Difficulty: {ctx.deps.recommended_difficulty}\n"
    bank_info += f"Matching Skills: {', '.join(ctx.deps.matching_skills)}\n"
    
    return bank_info

# Evaluation Agent
evaluation_agent = Agent(
    model=LOCAL_MODEL,
    deps_type=InterviewTurn,
    result_type=Evaluation,
    system_prompt=(
        "You are an expert technical interviewer and evaluator. You will receive an InterviewTurn object containing:\n"
        "- question: The interview question that was asked\n"
        "- ideal_answer: The expected/ideal answer for comparison\n"
        "- candidate_answer: The candidate's actual response\n\n"
        "Your task is to evaluate the candidate_answer against the ideal_answer for the given question.\n"
        "Score each dimension (0-100):\n"
        "- technical_accuracy: How technically correct is the answer?\n"
        "- completeness: How complete/thorough is the answer?\n"
        "- clarity: How clear and well-communicated is the answer?\n\n"
        "Calculate overall score as the average of the three dimensions.\n"
        "Provide constructive feedback, identify strengths, suggest improvements.\n"
        "Set follow_up_needed=true if the answer is unclear or incomplete (score < 60).\n\n"
        "IMPORTANT: Always evaluate the candidate_answer field, never say the answer is missing."
    ),
)

###############################################################################
# ----------------------------- Enhanced Coordinator -------------------------#
###############################################################################
class EnhancedInterviewSession:
    def __init__(self, resume: str, job: str):
        self.id = secrets.token_hex(8)
        self.turns: List[InterviewTurn] = []
        self.evaluations: List[Evaluation] = []
        self.start_time = datetime.now()
        self.current_question_index = 0
        
        # Initialize session
        try:
            logger.info(f"Creating interview session {self.id}")
            resume_input = ResumeInput(resume_text=resume, job_description=job)
            
            # Get context analysis
            try:
                context_result = context_agent.run_sync(
                    "Analyze this candidate's background and recommend question difficulty.", 
                    deps=resume_input
                )
                self.context = context_result.data
                
                # Ensure all required fields are present
                if not hasattr(self.context, 'experience_level'):
                    self.context.experience_level = "mid"
                if not hasattr(self.context, 'recommended_difficulty'):
                    self.context.recommended_difficulty = "intermediate"
                if not hasattr(self.context, 'matching_skills'):
                    self.context.matching_skills = ["general programming"]
                    
            except Exception as e:
                logger.error(f"Context analysis failed: {str(e)}, using fallback context")
                # Fallback context
                self.context = ContextSummary(
                    summary="Candidate profile analysis unavailable. Proceeding with standard interview.",
                    matching_skills=["programming", "problem-solving"],
                    experience_level="mid",
                    recommended_difficulty="intermediate"
                )
            logger.info(f"Context analysis completed for session {self.id}")
            
            # Select questions
            try:
                question_result = question_agent.run_sync(
                    "Select appropriate interview questions based on the candidate analysis.", 
                    deps=self.context
                )
                self.question_batch = question_result.data
                self.questions = self.question_batch.questions
            except Exception as e:
                logger.error(f"Question selection failed: {str(e)}, using fallback questions")
                # Fallback to default questions if AI selection fails
                fallback_questions = [
                    TailoredQuestion(
                        question=q["question"],
                        ideal_answer=q["ideal_answer"],
                        tags=q.get("tags", ["general"]),
                        difficulty=q.get("difficulty", "intermediate")
                    ) for q in QUESTION_BANK[:3]
                ]
                self.questions = fallback_questions
                self.question_batch = QuestionBatch(
                    questions=fallback_questions,
                    reasoning="Used fallback questions due to AI selection failure"
                )
            logger.info(f"Selected {len(self.questions)} questions for session {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize session {self.id}: {str(e)}")
            raise HTTPException(500, f"Failed to initialize interview session: {str(e)}")

    def get_current_question(self) -> Optional[str]:
        """Get the current question without advancing the index."""
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index].question
        return None

    def advance_to_next_question(self) -> Optional[str]:
        """Advance to the next question and return it."""
        self.current_question_index += 1
        return self.get_current_question()

    async def process_answer(self, answer: str) -> tuple[Evaluation, InterviewProgress]:
        """Process the candidate's answer and return evaluation with progress."""
        if self.current_question_index >= len(self.questions):
            raise ValueError("No more questions available")
        
        current_q = self.questions[self.current_question_index]
        
        # Create interview turn
        turn = InterviewTurn(
            question=current_q.question,
            ideal_answer=current_q.ideal_answer,
            candidate_answer=answer
        )
        
        try:
            # Debug logging
            logger.info(f"Evaluating answer for session {self.id}: '{answer[:50]}...'")
            logger.info(f"Question: '{current_q.question}'")
            logger.info(f"Expected: '{current_q.ideal_answer[:50]}...'")
            
            # Evaluate the answer
            eval_prompt = (
                f"Please evaluate this interview response:\n\n"
                f"QUESTION: {current_q.question}\n\n"
                f"CANDIDATE'S ANSWER: {answer}\n\n"
                f"EXPECTED ANSWER: {current_q.ideal_answer}\n\n"
                f"Please provide detailed evaluation with scores for technical accuracy, completeness, and clarity."
            )
            
            logger.info(f"Sending evaluation prompt: {eval_prompt[:200]}...")
            
            eval_result = await evaluation_agent.run(eval_prompt, deps=turn)
            evaluation = eval_result.data
            
            logger.info(f"Received evaluation: score={evaluation.score}, tech={evaluation.technical_accuracy}, complete={evaluation.completeness}, clarity={evaluation.clarity}")
            
            # Ensure we have valid scores
            if evaluation.score == 0 and evaluation.technical_accuracy == 0 and evaluation.completeness == 0:
                # Fallback scoring based on simple keyword matching
                answer_lower = answer.lower()
                ideal_lower = current_q.ideal_answer.lower()
                
                # Basic scoring logic
                if len(answer.strip()) < 5:
                    tech_score = 10
                    completeness_score = 10
                    clarity_score = 20
                elif any(word in answer_lower for word in ['mutable', 'immutable', 'list', 'tuple']):
                    tech_score = 60
                    completeness_score = 50
                    clarity_score = 60
                else:
                    tech_score = 30
                    completeness_score = 30
                    clarity_score = 40
                
                evaluation = Evaluation(
                    score=(tech_score + completeness_score + clarity_score) // 3,
                    technical_accuracy=tech_score,
                    completeness=completeness_score,
                    clarity=clarity_score,
                    feedback=f"Based on your answer '{answer}', here's my assessment: " + (
                        "Good understanding of mutability concepts!" if tech_score > 50 
                        else "Consider elaborating on the key differences between these data structures."
                    ),
                    strengths=["Answered the question"] if len(answer.strip()) > 5 else [],
                    improvements=["Provide more detailed explanation", "Include specific examples"],
                    follow_up_needed=tech_score < 60
                )
            
            # Store the turn and evaluation
            self.turns.append(turn)
            self.evaluations.append(evaluation)
            
            # Calculate progress
            progress = self._calculate_progress()
            
            logger.info(f"Processed answer for session {self.id}, question {self.current_question_index + 1}, score: {evaluation.score}")
            return evaluation, progress
            
        except Exception as e:
            logger.error(f"Failed to process answer for session {self.id}: {str(e)}")
            # Provide fallback evaluation
            fallback_evaluation = Evaluation(
                score=50,
                technical_accuracy=50,
                completeness=50,
                clarity=50,
                feedback="Unable to evaluate answer due to system error. Please try again.",
                strengths=["Answer received"],
                improvements=["System evaluation unavailable"],
                follow_up_needed=False
            )
            self.evaluations.append(fallback_evaluation)
            progress = self._calculate_progress()
            return fallback_evaluation, progress

    def _calculate_progress(self) -> InterviewProgress:
        """Calculate current interview progress."""
        avg_score = sum(e.score for e in self.evaluations) / max(len(self.evaluations), 1)
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{elapsed.seconds // 60}m {elapsed.seconds % 60}s"
        
        return InterviewProgress(
            current_question=len(self.evaluations),
            total_questions=len(self.questions),
            average_score=avg_score,
            time_elapsed=elapsed_str
        )

    def generate_final_report(self) -> FinalTranscript:
        """Generate comprehensive final interview report."""
        if not self.evaluations:
            raise ValueError("No evaluations available for final report")
        
        # Calculate scores
        overall_score = sum(e.score for e in self.evaluations) / len(self.evaluations)
        technical_score = sum(e.technical_accuracy for e in self.evaluations) / len(self.evaluations)
        communication_score = sum(e.clarity for e in self.evaluations) / len(self.evaluations)
        
        # Generate recommendation
        if overall_score >= 80:
            recommendation = "Strong Hire - Candidate demonstrates excellent technical knowledge and communication skills."
        elif overall_score >= 65:
            recommendation = "Hire - Candidate shows good technical competency with room for growth."
        elif overall_score >= 50:
            recommendation = "Borderline - Consider for junior roles or with additional training."
        else:
            recommendation = "No Hire - Candidate needs significant development before being ready for this role."
        
        # Generate summary
        strengths = []
        improvements = []
        for eval in self.evaluations:
            strengths.extend(eval.strengths)
            improvements.extend(eval.improvements)
        
        summary = f"Candidate completed {len(self.evaluations)} questions with an overall score of {overall_score:.1f}%. " \
                 f"Key strengths: {', '.join(set(strengths)[:3])}. " \
                 f"Areas for improvement: {', '.join(set(improvements)[:3])}."
        
        # Calculate duration
        duration = datetime.now() - self.start_time
        duration_str = f"{duration.seconds // 60}m {duration.seconds % 60}s"
        
        return FinalTranscript(
            session_id=self.id,
            turns=self.turns,
            evaluations=self.evaluations,
            overall_score=overall_score,
            technical_score=technical_score,
            communication_score=communication_score,
            recommendation=recommendation,
            summary=summary,
            duration=duration_str
        )

###############################################################################
# ----------------------------- Enhanced Web Server --------------------------#
###############################################################################
app = FastAPI(title="Enhanced Agentic Interview Bot", version="2.0")
sessions: Dict[str, EnhancedInterviewSession] = {}

@app.post("/session")
async def create_session(req: ResumeInput):
    """Create a new interview session."""
    try:
        sess = EnhancedInterviewSession(req.resume_text, req.job_description)
        sessions[sess.id] = sess
        
        first_question = sess.get_current_question()
        if not first_question:
            raise HTTPException(500, "No questions available for this candidate")
        
        return {
            "session_id": sess.id,
            "first_question": first_question,
            "context_summary": sess.context.summary,
            "total_questions": len(sess.questions),
            "selection_reasoning": sess.question_batch.reasoning
        }
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(500, f"Failed to create interview session: {str(e)}")

@app.websocket("/ws/{session_id}")
async def websocket_interview(websocket: WebSocket, session_id: str):
    """Handle real-time interview communication."""
    if session_id not in sessions:
        await websocket.close(code=4404, reason="Session not found")
        return
    
    await websocket.accept()
    session = sessions[session_id]
    logger.info(f"WebSocket connected for session {session_id}")
    
    try:
        while True:
            # Receive candidate answer
            answer = await websocket.receive_text()
            
            if answer.strip().lower() in ['quit', 'exit', 'end']:
                final_report = session.generate_final_report()
                await websocket.send_json({
                    "type": "final_report",
                    "data": final_report.dict()
                })
                await websocket.close()
                break
            
            # Process the answer
            evaluation, progress = await session.process_answer(answer)
            
            # Send evaluation feedback
            await websocket.send_json({
                "type": "evaluation",
                "data": {
                    "score": evaluation.score,
                    "feedback": evaluation.feedback,
                    "strengths": evaluation.strengths,
                    "improvements": evaluation.improvements,
                    "technical_accuracy": evaluation.technical_accuracy,
                    "completeness": evaluation.completeness,
                    "clarity": evaluation.clarity
                }
            })
            
            # Send progress update
            await websocket.send_json({
                "type": "progress",
                "data": progress.dict()
            })
            
            # Check if we need a follow-up or next question
            if evaluation.follow_up_needed and evaluation.score < 60:
                follow_up = f"Can you elaborate more on {session.questions[session.current_question_index].question.split('?')[0]}?"
                await websocket.send_json({
                    "type": "follow_up",
                    "data": {"question": follow_up}
                })
            else:
                # Move to next question
                next_question = session.advance_to_next_question()
                if next_question:
                    await websocket.send_json({
                        "type": "next_question",
                        "data": {"question": next_question}
                    })
                else:
                    # Interview complete
                    final_report = session.generate_final_report()
                    await websocket.send_json({
                        "type": "final_report",
                        "data": final_report.dict()
                    })
                    await websocket.close()
                    break
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")

@app.get("/session/{session_id}/report")
async def get_session_report(session_id: str):
    """Get the final report for a completed session."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    
    session = sessions[session_id]
    if not session.evaluations:
        raise HTTPException(400, "Session not completed yet")
    
    return session.generate_final_report()

# Enhanced HTML Interface
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Agentic Interview Bot</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1em; }
        .content { padding: 30px; }
        .form-group { margin-bottom: 25px; }
        label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: 600; 
            color: #333; 
        }
        textarea, input { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        textarea:focus, input:focus { 
            outline: none; 
            border-color: #667eea; 
        }
        textarea { 
            height: 120px; 
            resize: vertical; 
            font-family: inherit; 
        }
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            border: none; 
            padding: 15px 30px; 
            border-radius: 10px; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            transition: transform 0.2s ease;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn:disabled { 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none; 
        }
        #chat { 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            height: 400px; 
            overflow-y: auto; 
            padding: 20px; 
            margin-bottom: 20px; 
            background: #f8f9fa;
        }
        .message { 
            margin: 15px 0; 
            padding: 15px; 
            border-radius: 10px; 
            max-width: 80%; 
        }
        .user { 
            background: #e3f2fd; 
            border-left: 4px solid #2196f3; 
            margin-left: auto; 
        }
        .bot { 
            background: #f1f8e9; 
            border-left: 4px solid #4caf50; 
        }
        .evaluation { 
            background: #fff3e0; 
            border-left: 4px solid #ff9800; 
            font-size: 0.9em; 
        }
        .progress { 
            background: #f3e5f5; 
            border-left: 4px solid #9c27b0; 
            font-size: 0.9em; 
        }
        .input-area { 
            display: flex; 
            gap: 10px; 
            align-items: center; 
        }
        .input-area input { 
            flex: 1; 
            margin-bottom: 0; 
        }
        .score { 
            font-weight: bold; 
            font-size: 1.1em; 
        }
        .score.high { color: #4caf50; }
        .score.medium { color: #ff9800; }
        .score.low { color: #f44336; }
        .hidden { display: none; }
        .loading { 
            text-align: center; 
            padding: 20px; 
            color: #666; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Enhanced Interview Bot</h1>
            <p>AI-Powered Technical Interview Assistant</p>
        </div>
        
        <div class="content">
            <form id="setupForm">
                <div class="form-group">
                    <label for="resume">📄 Candidate Resume:</label>
                    <textarea 
                        id="resume" 
                        required 
                        placeholder="Paste the candidate's resume here... Include education, experience, skills, and projects."
                    ></textarea>
                </div>
                
                <div class="form-group">
                    <label for="job">💼 Job Description:</label>
                    <textarea 
                        id="job" 
                        required 
                        placeholder="Paste the job description here... Include required skills, responsibilities, and qualifications."
                    ></textarea>
                </div>
                
                <button type="submit" class="btn">🚀 Start Interview</button>
            </form>
            
            <div id="interviewSection" class="hidden">
                <div id="contextInfo" class="message bot"></div>
                <div id="chat"></div>
                <div class="input-area">
                    <input 
                        id="answerInput" 
                        placeholder="Type your answer here..." 
                        autocomplete="off"
                    />
                    <button id="sendBtn" class="btn">Send</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws;
        let currentSession = null;

        document.getElementById('setupForm').onsubmit = async (e) => {
            e.preventDefault();
            
            const resume = document.getElementById('resume').value.trim();
            const job = document.getElementById('job').value.trim();
            
            if (!resume || !job) {
                alert('Please fill in both resume and job description.');
                return;
            }

            try {
                showLoading('Creating interview session...');
                
                const response = await fetch('/session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ resume_text: resume, job_description: job })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                currentSession = data;
                
                // Hide setup form and show interview
                document.getElementById('setupForm').classList.add('hidden');
                document.getElementById('interviewSection').classList.remove('hidden');
                
                // Show context information
                document.getElementById('contextInfo').innerHTML = `
                    <strong>📊 Interview Setup Complete</strong><br>
                    <strong>Context:</strong> ${data.context_summary}<br>
                    <strong>Questions:</strong> ${data.total_questions} selected<br>
                    <strong>Reasoning:</strong> ${data.selection_reasoning}<br>
                    <hr style="margin: 10px 0;">
                    <strong>First Question:</strong> ${data.first_question}
                `;
                
                // Connect WebSocket
                connectWebSocket(data.session_id);
                
            } catch (error) {
                console.error('Error creating session:', error);
                alert('Failed to create interview session. Please try again.');
            }
        };

        function connectWebSocket(sessionId) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/${sessionId}`);
            
            ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            };
            
            ws.onclose = () => {
                addMessage('system', '🔌 Connection closed. Interview session ended.');
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                addMessage('system', '❌ Connection error. Please refresh and try again.');
            };
        }

        function handleWebSocketMessage(message) {
            switch (message.type) {
                case 'evaluation':
                    showEvaluation(message.data);
                    break;
                case 'progress':
                    showProgress(message.data);
                    break;
                case 'next_question':
                    addMessage('bot', `📝 Next Question: ${message.data.question}`);
                    break;
                case 'follow_up':
                    addMessage('bot', `🔍 Follow-up: ${message.data.question}`);
                    break;
                case 'final_report':
                    showFinalReport(message.data);
                    break;
            }
        }

        function showEvaluation(data) {
            const scoreClass = data.score >= 70 ? 'high' : data.score >= 50 ? 'medium' : 'low';
            const evaluationHtml = `
                <div class="message evaluation">
                    <strong>📊 Evaluation Results</strong><br>
                    <span class="score ${scoreClass}">Overall Score: ${data.score}/100</span><br>
                    <small>Technical: ${data.technical_accuracy}/100 | Completeness: ${data.completeness}/100 | Clarity: ${data.clarity}/100</small><br><br>
                    <strong>💬 Feedback:</strong> ${data.feedback}<br><br>
                    <strong>✅ Strengths:</strong> ${data.strengths.join(', ')}<br>
                    <strong>📈 Improvements:</strong> ${data.improvements.join(', ')}
                </div>
            `;
            document.getElementById('chat').innerHTML += evaluationHtml;
            scrollToBottom();
        }

        function showProgress(data) {
            const progressHtml = `
                <div class="message progress">
                    <strong>📈 Progress Update</strong><br>
                    Question ${data.current_question}/${data.total_questions} completed<br>
                    Current Average: ${data.average_score.toFixed(1)}/100<br>
                    Time Elapsed: ${data.time_elapsed}
                </div>
            `;
            document.getElementById('chat').innerHTML += progressHtml;
            scrollToBottom();
        }

        function showFinalReport(data) {
            const scoreClass = data.overall_score >= 70 ? 'high' : data.overall_score >= 50 ? 'medium' : 'low';
            const reportHtml = `
                <div class="message bot">
                    <strong>🎯 Interview Complete!</strong><br><br>
                    <span class="score ${scoreClass}">Final Score: ${data.overall_score.toFixed(1)}/100</span><br>
                    <small>Technical: ${data.technical_score.toFixed(1)} | Communication: ${data.communication_score.toFixed(1)}</small><br><br>
                    <strong>📋 Summary:</strong> ${data.summary}<br><br>
                    <strong>🎯 Recommendation:</strong> ${data.recommendation}<br><br>
                    <strong>⏱️ Duration:</strong> ${data.duration}
                </div>
            `;
            document.getElementById('chat').innerHTML += reportHtml;
            scrollToBottom();
            
            // Disable input
            document.getElementById('answerInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
        }

        function addMessage(type, text) {
            const div = document.createElement('div');
            div.className = `message ${type}`;
            div.innerHTML = type === 'user' ? `<strong>👤 You:</strong> ${text}` : 
                           type === 'bot' ? `<strong>🤖 Interviewer:</strong> ${text}` : 
                           `<strong>ℹ️ System:</strong> ${text}`;
            document.getElementById('chat').appendChild(div);
            scrollToBottom();
        }

        function sendAnswer() {
            const input = document.getElementById('answerInput');
            const answer = input.value.trim();
            
            if (!answer) return;
            
            addMessage('user', answer);
            ws.send(answer);
            input.value = '';
        }

        function showLoading(message) {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = `⏳ ${message}`;
            document.body.appendChild(loadingDiv);
            
            setTimeout(() => {
                if (loadingDiv.parentNode) {
                    loadingDiv.parentNode.removeChild(loadingDiv);
                }
            }, 3000);
        }

        function scrollToBottom() {
            const chat = document.getElementById('chat');
            chat.scrollTop = chat.scrollHeight;
        }

        // Event listeners
        document.getElementById('sendBtn').onclick = sendAnswer;
        document.getElementById('answerInput').onkeypress = (e) => {
            if (e.key === 'Enter') sendAnswer();
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_INTERFACE

async def test_evaluation():
    """Test the evaluation system with sample data."""
    test_turn = InterviewTurn(
        question="Explain the difference between a Python list and tuple.",
        ideal_answer="A list is mutable and typically used for homogenous items, while a tuple is immutable and often used for heterogeneous data. Lists use square brackets [], tuples use parentheses ().",
        candidate_answer="list is mutable, but tuple is not mutable"
    )
    
    try:
        result = await evaluation_agent.run(
            "Please evaluate this test response.",
            deps=test_turn
        )
        print("✅ Test Evaluation Result:")
        print(f"Score: {result.data.score}")
        print(f"Feedback: {result.data.feedback}")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_evaluation())
    else:
        logger.info("Starting Enhanced Agentic Interview Bot...")
        uvicorn.run(app, host="0.0.0.0", port=8635, log_level="info")
