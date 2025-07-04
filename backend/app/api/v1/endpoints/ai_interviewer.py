from __future__ import annotations
import secrets, asyncio, logging, json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Union
from contextlib import contextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from sqlmodel import Session, select

from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from core.database import get_session
from models.models import (
    Application,
    Candidate,
    Interview,
    Job,
    Match,
)

# ───────── LOGGING SETUP ──────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ────── MODEL PROVIDERS ──────────
LOCAL_PROVIDER = OpenAIProvider(base_url="http://ollama:11439/v1")
DEFAULT_MODEL_ID = "ollama/qwen3:8b"
MODEL_NAME = DEFAULT_MODEL_ID.split("ollama/")[1]
LOCAL_MODEL = OpenAIModel(model_name=MODEL_NAME, provider=LOCAL_PROVIDER)
# MODEL_NAME = "mistralai/mistral-small-3.2-24b-instruct:free"
# LOCAL_MODEL = OpenAIModel(model_name=MODEL_NAME,provider=OpenRouterProvider(api_key="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"))
# ───────── Pydantic MODELS ─────────
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

@dataclass
class ConversationEntry:
    """Represents a single message in the conversation"""
    speaker: str  # 'interviewer' or 'candidate'
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str | None = None  # 'question', 'clarification', 'warning', 'answer', 'followup'

class InterviewTurn(BaseModel):
    question: str
    ideal_answer: str
    candidate_answer: str
    followup_question: str | None = None
    followup_answer: str | None = None
    followup_reason: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    response_time_seconds: float
    followup_response_time_seconds: float | None = None
    paste_count: int = 0
    tab_switch_count: int = 0
    copy_count: int = 0
    # NEW: Full conversation history for this turn
    conversation_history: list[dict] = Field(default_factory=list)  # List of ConversationEntry dicts

class Evaluation(BaseModel):
    technical_score: int
    communication_score: int  # assesses interaction quality and language clarity
    feedback: str
    strengths: list[str]
    improvements: list[str]
    classification: ResponseType
    explanation: str

class FinalReport(BaseModel):
    session_id: str
    turns: list[InterviewTurn]
    evaluations: list[Evaluation]
    overall_score: float
    technical_score: float
    communication_score: float
    duration: str
    followup_question: str | None = None

class ResponseType(str, Enum):
    answer = 'answer'
    clarification = 'clarification'
    unrelated = 'unrelated'

class ClassificationOutput(BaseModel):
    classification: ResponseType
    explanation: str

class FollowUpDecision(BaseModel):
    needs_followup: bool
    followup_question: str | None = None
    reason: str

# ───────── Agents ─────────
evaluation_agent = Agent(
    LOCAL_MODEL,
    deps_type=InterviewTurn,
    output_type=Evaluation,
    system_prompt="""
You are an expert interview evaluator with deep expertise in technical assessment and candidate evaluation.

OUTPUT JSON FIELDS:
- technical_score: 0-100 evaluating technical depth & correctness
- communication_score: 0-100 evaluating interaction style, clarity, language use, structure
- feedback: 2-3 sentence summary covering tech & communication aspects
- strengths: list of strengths
- improvements: list of areas to improve

SCORING GUIDANCE:
• Technical (70% weight): accuracy, depth, practical insight
• Communication (30% weight): clarity, structured reasoning, engaging with AI (asking clarifications, logical flow)
""",
    result_retries=3
)

follow_up_agent = Agent(
    LOCAL_MODEL,
    output_type=FollowUpDecision,
    system_prompt="""
You are an expert technical interviewer specializing in deep assessment through strategic follow-up questions. Your PRIMARY GOAL is to ask a follow-up ONLY when the candidate's answer is vague, superficial, or clearly missing critical context.

STRICT MINIMUM RULE:
- If the answer is clear, detailed, and demonstrates solid understanding, set needs_followup=false.
- If you are UNCERTAIN, default to needs_followup=false.
- Favour NOT asking a follow-up unless it will significantly improve your confidence in the assessment.

ASK FOLLOW-UP when (one or more):
1. Core concept is mentioned but not explained (e.g., 'I would use caching' with no details).
2. Answer is under-specified (< 3 sentences) and lacks concrete examples.
3. Candidate lists buzzwords without describing HOW or WHY.
4. Response is partially correct but omits key trade-offs / edge cases.
5. The question explicitly required step-by-step reasoning which is missing.

DO NOT ASK FOLLOW-UP when:
- Answer provides step-by-step reasoning with examples or metrics.
- Candidate thoroughly explains trade-offs and implementation details.
- Answer is obviously wrong or off-topic (just move on).
- Time/flow efficiency indicates moving to next question.

FOLLOW-UP QUESTION STYLE (when needed):
- ONE short, precise question (max 25 words).
- Target exactly the missing detail.
- Open-ended (avoid yes/no).

OUTPUT JSON FIELDS:
- needs_followup: true | false
- followup_question: string | null (null if needs_followup=false)
- reason: VERY brief (max 15 words).
""",
    result_retries=3
)

classification_agent = Agent(
    LOCAL_MODEL,
    output_type=ClassificationOutput,
    system_prompt=(
        "You are an intelligent conversation classifier for technical interviews. "
        "Your role is to accurately categorize candidate responses and guide the interview flow appropriately.\n\n"
        
        "CLASSIFICATION CATEGORIES:\n\n"
        
        "1. 'answer' - The candidate is attempting to answer the question:\n"
        "   - Contains technical content related to the question\n"
        "   - Shows effort to address what was asked\n"
        "   - May be incomplete, incorrect, or partial, but is a genuine attempt\n"
        "   - Includes follow-up questions that show engagement with the topic\n\n"
        
        "2. 'clarification' - The candidate needs help understanding the question:\n"
        "   - Asks for specific details about the question\n"
        "   - Requests examples or context\n"
        "   - Seeks clarification on terminology or scope\n"
        "   - Shows willingness to answer but needs guidance\n\n"
        
        "3. 'unrelated' - The response is off-topic or inappropriate:\n"
        "   - Discusses topics completely unrelated to the question\n"
        "   - Personal anecdotes without technical relevance\n"
        "   - Attempts to change the subject\n"
        "   - Non-professional or inappropriate content\n\n"
        
        "RESPONSE GUIDELINES:\n\n"
        
        "For 'answer' classification:\n"
        "- explanation: Brief acknowledgment like 'Candidate provided a technical response' or 'Attempting to answer the question'\n\n"
        
        "For 'clarification' classification:\n"
        "- explanation: Restate the question in simpler terms, provide context, or offer an example\n"
        "- Be helpful and encouraging\n"
        "- Break down complex questions into components\n"
        "- Provide just enough guidance without giving away the answer\n\n"
        
        "For 'unrelated' classification:\n"
        "- explanation: Politely redirect to the question at hand\n"
        "- Be professional and respectful\n"
        "- Restate the original question clearly\n"
        "- Encourage focus on the technical topic\n\n"
        
        "DECISION PRINCIPLES:\n"
        "- When in doubt between 'answer' and 'clarification', lean toward 'answer'\n"
        "- Look for any technical keywords or concepts that relate to the question\n"
        "- Consider the candidate's intent, not just the quality of their response\n"
        "- Be generous in allowing attempts to answer, even if incomplete\n"
        "- Only use 'unrelated' for clearly off-topic responses\n\n"
        
        "Maintain a supportive interview environment while ensuring productive conversation flow."
    ),
    result_retries=3
)

# ───────── SHARED STATE ─────────
@dataclass
class InterviewState:
    interview: Interview
    job: Job
    candidate: Candidate
    application: Application
    context: ContextSummary | None = None
    questions: list[TailoredQuestion] = field(default_factory=list)
    turns: list[InterviewTurn] = field(default_factory=list)
    evaluations: list[Evaluation] = field(default_factory=list)
    i: int = 0  # Current question index
    ws: WebSocket | None = None
    start_time: datetime = field(default_factory=datetime.now)
    session_id: str = field(init=False)  # Will be set from email
    _answer: str | None = None
    _t_question: datetime | None = None
    _classification: ClassificationOutput | None = None
    _followup_decision: FollowUpDecision | None = None
    _is_followup: bool = False  # Track if current question is a follow-up
    _current_turn: InterviewTurn | None = None  # Track current turn being built
    _paste_count: int = 0
    _tab_switch_count: int = 0
    _copy_count: int = 0
    # NEW: Current turn conversation history
    _current_conversation: list[ConversationEntry] = field(default_factory=list)
    
    def __post_init__(self):
        # Use email as session_id
        self.session_id = str(self.interview.id)
    
    def add_conversation_entry(self, speaker: str, message: str, message_type: str | None = None):
        """Add an entry to the current turn's conversation history"""
        entry = ConversationEntry(
            speaker=speaker,
            message=message,
            message_type=message_type
        )
        self._current_conversation.append(entry)
    
    def get_conversation_context(self) -> str:
        """Get formatted conversation history for the current turn"""
        if not self._current_conversation:
            return "No conversation history yet."
        
        context = "=== CONVERSATION HISTORY FOR THIS TURN ===\n"
        for entry in self._current_conversation:
            speaker_label = "🤖 AI Interviewer" if entry.speaker == "interviewer" else "👤 Candidate"
            context += f"{speaker_label} ({entry.message_type or 'message'}): {entry.message}\n"
        return context + "\n"
    
    def reset_conversation_for_new_turn(self):
        """Reset conversation history when starting a new turn"""
        self._current_conversation = []

# ───────── LIVE INTERVIEW GRAPH ─────────
@dataclass
class AskQuestion(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> "AwaitResponse":
        q = ctx.state.questions[ctx.state.i]
        ctx.state._t_question = datetime.now()
        
        # Reset conversation history for new turn
        ctx.state.reset_conversation_for_new_turn()
        
        # Add question to conversation history
        ctx.state.add_conversation_entry("interviewer", q.question, "question")
        
        logger.info(f"❓ Asking question {ctx.state.i + 1}/{len(ctx.state.questions)} in session {ctx.state.session_id}")
        logger.info(f"Question: {q.question}")
        logger.info(f"Expected difficulty: {q.difficulty}")
        await ctx.state.ws.send_json({'question': q.question})
        return AwaitResponse()

@dataclass
class AwaitResponse(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> "ClassifyResponse":
        logger.info(f"⏳ Waiting for candidate response in session {ctx.state.session_id}")
        # Receive JSON with answer and optional metrics
        msg = await ctx.state.ws.receive_text()
        try:
            data = json.loads(msg)
            answer = data["answer"]
            paste_count = int(data.get("paste_count", 0))
            tab_switch_count = int(data.get("tab_switch_count", 0))
            copy_count = int(data.get("copy_count", 0))
        except Exception:
            answer = msg
            paste_count = 0
            tab_switch_count = 0
            copy_count = 0
        ctx.state._answer = answer
        ctx.state._paste_count = paste_count
        ctx.state._tab_switch_count = tab_switch_count
        ctx.state._copy_count = copy_count
        
        # Add candidate response to conversation history
        ctx.state.add_conversation_entry("candidate", answer, "response")
        
        response_time = (datetime.now() - ctx.state._t_question).total_seconds()
        logger.info(f"💬 Received candidate response in {response_time:.1f}s (paste: {paste_count}, tab: {tab_switch_count}, copy: {copy_count})")
        logger.info(f"Response length: {len(ctx.state._answer)} characters")
        logger.info(f"Response preview: {ctx.state._answer[:100]}...")
        return ClassifyResponse()

@dataclass
class ClassifyResponse(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> Union[
        "SendClarification", "SendWarning", "CheckFollowUp"
    ]:
        q = ctx.state.questions[ctx.state.i]
        logger.info(f"🔍 Classifying response for session {ctx.state.session_id}")
        
        # Enhanced classification prompt with full conversation context
        classification_prompt = (
            "Classify this candidate's response in the context of a technical interview:\n\n"
            "=== INTERVIEW QUESTION ===\n"
            f"Question: {q.question}\n"
            f"Difficulty: {q.difficulty}\n"
            f"Expected Topics: {', '.join(q.tags)}\n\n"
            f"{ctx.state.get_conversation_context()}"
            "=== CLASSIFICATION TASK ===\n"
            "Determine if this response is:\n"
            "- 'answer': Attempting to address the question (even if incomplete/incorrect)\n"
            "- 'clarification': Asking for help understanding the question\n"
            "- 'unrelated': Off-topic or inappropriate content\n\n"
            "Consider the candidate's intent, any technical keywords they use, and the full conversation context above."
            "Only use 'unrelated' if the response is completely off-topic or inappropriate."
            "if the user told you he does not know the answer, then you should use 'answer'"
        )
        
        res = await classification_agent.run(classification_prompt)
        ctx.state._classification = res.output
        logger.info(f"📊 Classification result: {res.output.classification}")
        logger.info(f"Classification explanation: {res.output.explanation}")
        
        if res.output.classification == ResponseType.answer:
            logger.info("✅ Response classified as answer - checking for follow-up needs")
            return CheckFollowUp()
        elif res.output.classification == ResponseType.clarification:
            logger.info("❓ Response classified as clarification request")
            return SendClarification()
        else:
            logger.info("⚠️ Response classified as unrelated")
            return SendWarning()

@dataclass
class SendClarification(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> AwaitResponse:
        clarification = ctx.state._classification.explanation
        
        # Add clarification to conversation history
        ctx.state.add_conversation_entry("interviewer", clarification, "clarification")
        
        logger.info(f"💡 Sending clarification for session {ctx.state.session_id}")
        logger.info(f"Clarification: {clarification}")
        await ctx.state.ws.send_json({'clarification': clarification})
        return AwaitResponse()

@dataclass
class SendWarning(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> AwaitResponse:
        warning = ctx.state._classification.explanation
        
        # Add warning to conversation history
        ctx.state.add_conversation_entry("interviewer", warning, "warning")
        
        logger.info(f"⚠️ Sending warning for session {ctx.state.session_id}")
        logger.info(f"Warning: {warning}")
        await ctx.state.ws.send_json({'warning': warning})
        return AwaitResponse()

@dataclass
class CheckFollowUp(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> Union["AskFollowUp", "EvaluateAnswer"]:
        # Don't ask follow-up for follow-up questions to avoid infinite loops
        if ctx.state._is_followup:
            logger.info(f"⏭️ Skipping follow-up check - current question was already a follow-up")
            return EvaluateAnswer()
        
        q = ctx.state.questions[ctx.state.i]
        
        logger.info(f"🔍 Checking if follow-up question needed for session {ctx.state.session_id}")
        
        # Create initial turn object
        if not ctx.state._current_turn:
            ctx.state._current_turn = InterviewTurn(
                question=q.question,
                ideal_answer=q.ideal_answer,
                candidate_answer=ctx.state._answer,
                response_time_seconds=(datetime.now() - ctx.state._t_question).total_seconds(),
                paste_count=getattr(ctx.state, '_paste_count', 0),
                tab_switch_count=getattr(ctx.state, '_tab_switch_count', 0),
                copy_count=getattr(ctx.state, '_copy_count', 0)
            )
        
        # Enhanced follow-up decision prompt with full conversation context
        followup_prompt = (
            "Analyze this interview interaction to determine if a follow-up question would provide valuable additional insight:\n\n"
            "=== ORIGINAL QUESTION ===\n"
            f"Question: {q.question}\n"
            f"Difficulty: {q.difficulty}\n"
            f"Topics: {', '.join(q.tags)}\n\n"
            "=== IDEAL ANSWER ===\n"
            f"{q.ideal_answer}\n\n"
            f"{ctx.state.get_conversation_context()}"
            "=== CANDIDATE CONTEXT ===\n"
            f"Experience Level: {ctx.state.context.experience_level}\n"
            f"Current Question: {ctx.state.i + 1}/{len(ctx.state.questions)}\n\n"
            "=== DECISION CRITERIA ===\n"
            "Consider whether a follow-up question would:\n"
            "- Reveal deeper understanding or expose knowledge gaps\n"
            "- Clarify ambiguous or incomplete responses\n"
            "- Test practical application of mentioned concepts\n"
            "- Explore problem-solving approach in more detail\n\n"
            "Balance thoroughness with interview efficiency. "
            "Focus on areas where additional probing would provide the most valuable assessment data.\n"
            "IMPORTANT: Consider the full conversation context above, including any clarifications or warnings that were given."
            "IMPORTANT: if the user told you he does not know the answer, then you should use 'not ask for follow up'"
        )
        
        result = await follow_up_agent.run(followup_prompt)
        ctx.state._followup_decision = result.output
        
        logger.info(f"🤔 Follow-up decision: {result.output.needs_followup}")
        logger.info(f"Reason: {result.output.reason}")
        
        if result.output.needs_followup and result.output.followup_question:
            logger.info(f"❓ Follow-up question: {result.output.followup_question}")
            # Add follow-up info to current turn
            ctx.state._current_turn.followup_question = result.output.followup_question
            ctx.state._current_turn.followup_reason = result.output.reason
            return AskFollowUp()
        else:
            logger.info("➡️ No follow-up needed, proceeding to evaluation")
            return EvaluateAnswer()

@dataclass
class AskFollowUp(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> "AwaitResponse":
        ctx.state._t_question = datetime.now()
        ctx.state._is_followup = True  # Mark as follow-up question
        
        followup_question = ctx.state._followup_decision.followup_question
        
        # Add follow-up question to conversation history
        ctx.state.add_conversation_entry("interviewer", followup_question, "followup")
        
        logger.info(f"🔄 Asking follow-up question in session {ctx.state.session_id}")
        logger.info(f"Follow-up: {followup_question}")
        
        await ctx.state.ws.send_json({
            'followup_question': followup_question,
            'reason': ctx.state._followup_decision.reason
        })
        return AwaitResponse()

@dataclass
class EvaluateAnswer(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> "NextQuestion":
        q = ctx.state.questions[ctx.state.i]
        
        # Handle follow-up answer if this is a follow-up response
        if ctx.state._is_followup and ctx.state._current_turn:
            # Add follow-up answer to current turn
            ctx.state._current_turn.followup_answer = ctx.state._answer
            ctx.state._current_turn.followup_response_time_seconds = (
                datetime.now() - ctx.state._t_question
            ).total_seconds()
            ctx.state._current_turn.paste_count = getattr(ctx.state, '_paste_count', 0)
            ctx.state._current_turn.tab_switch_count = getattr(ctx.state, '_tab_switch_count', 0)
            ctx.state._current_turn.copy_count = getattr(ctx.state, '_copy_count', 0)
            logger.info(f"📝 Recording follow-up answer for session {ctx.state.session_id}")
            ctx.state._is_followup = False  # Reset flag
        
        # Use current turn or create new one if not exists
        if not ctx.state._current_turn:
            ctx.state._current_turn = InterviewTurn(
                question=q.question,
                ideal_answer=q.ideal_answer,
                candidate_answer=ctx.state._answer,
                response_time_seconds=(datetime.now() - ctx.state._t_question).total_seconds(),
                paste_count=getattr(ctx.state, '_paste_count', 0),
                tab_switch_count=getattr(ctx.state, '_tab_switch_count', 0),
                copy_count=getattr(ctx.state, '_copy_count', 0)
            )
        
        t = ctx.state._current_turn
        
        logger.info(f"📝 Evaluating complete interaction for session {ctx.state.session_id}")
        logger.info(f"Original response time: {t.response_time_seconds:.1f} seconds")
        if t.followup_answer:
            logger.info(f"Follow-up response time: {t.followup_response_time_seconds:.1f} seconds")
        
        # Save conversation history to turn before evaluation
        t.conversation_history = [
            {
                "speaker": entry.speaker,
                "message": entry.message,
                "message_type": entry.message_type,
                "timestamp": entry.timestamp.isoformat()
            }
            for entry in ctx.state._current_conversation
        ]
        
        evaluation_prompt = (
            "Evaluate this candidate's complete response interaction in a technical interview context:\n\n"
            "=== QUESTION DETAILS ===\n"
            f"Question: {t.question}\n"
            f"Difficulty Level: {q.difficulty}\n"
            f"Topic Tags: {', '.join(q.tags)}\n"
            f"Original Response Time: {t.response_time_seconds:.1f} seconds\n"
            + (f"Follow-up Response Time: {t.followup_response_time_seconds:.1f} seconds\n" if t.followup_response_time_seconds else "") +
            "\n=== IDEAL ANSWER ===\n"
            f"{t.ideal_answer}\n\n"
            f"{ctx.state.get_conversation_context()}"
            "=== EVALUATION CONTEXT ===\n"
            f"Candidate Experience: {ctx.state.context.experience_level}\n"
            f"Relevant Skills: {', '.join(ctx.state.context.matching_skills)}\n\n"
            "=== EVALUATION CRITERIA ===\n"
            "Assess the complete interaction based on:\n"
            "1. Technical accuracy and correctness\n"
            "2. Depth of understanding demonstrated\n"
            "3. Communication clarity and structure\n"
            "4. Practical application awareness\n"
            "5. Response to follow-up questions (if applicable)\n"
            "6. How well they handled clarifications or warnings\n\n"
            "Consider the candidate's experience level when scoring. "
            "Evaluate the ENTIRE conversation flow above, including how the candidate responded to clarifications, warnings, or follow-up questions. "
            "Provide constructive feedback that helps them improve."
        )
        
        ev = await evaluation_agent.run(evaluation_prompt, deps=t)
        
        # Save the complete turn and evaluation
        ctx.state.turns.append(t)
        ctx.state.evaluations.append(ev.output)
        ctx.state._current_turn = None  # Reset for next question
        
        overall_local = (ev.output.technical_score + ev.output.communication_score) / 2
        logger.info(
            f"📊 Evaluation complete - Tech: {ev.output.technical_score}  Comm: {ev.output.communication_score}  Overall: {overall_local:.1f}"
        )
        logger.info(f"Feedback: {ev.output.feedback[:100]}...")
        logger.info(f"Strengths: {', '.join(ev.output.strengths)}")
        
        eval_payload = ev.output.model_dump()
        eval_payload['overall'] = overall_local
        await ctx.state.ws.send_json({'evaluation': eval_payload})
        return NextQuestion()

@dataclass
class NextQuestion(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> Union[AskQuestion, "EndInterview"]:
        ctx.state.i += 1
        if ctx.state.i < len(ctx.state.questions):
            logger.info(f"➡️ Moving to next question ({ctx.state.i + 1}/{len(ctx.state.questions)}) in session {ctx.state.session_id}")
            return AskQuestion()
        else:
            logger.info(f"🏁 All questions completed for session {ctx.state.session_id} - ending interview")
            return EndInterview()

@dataclass
class EndInterview(BaseNode[InterviewState]):
    async def run(self, ctx: GraphRunContext) -> End[InterviewState]:
        if ctx.state.evaluations:
            tech = sum(e.technical_score for e in ctx.state.evaluations) / len(ctx.state.evaluations)
            comm = sum(e.communication_score for e in ctx.state.evaluations) / len(ctx.state.evaluations)
            overall = (tech + comm) / 2
        else:
            overall = tech = comm = 0.0
        duration = datetime.now() - ctx.state.start_time
        
        logger.info(f"📊 Generating final report for session {ctx.state.session_id}")
        logger.info(f"Overall score: {overall:.1f}/100")
        logger.info(f"Total questions answered: {len(ctx.state.turns)}")
        logger.info(f"Interview duration: {duration}")
        
        report = FinalReport(
            session_id=ctx.state.session_id,
            turns=ctx.state.turns,
            evaluations=ctx.state.evaluations,
            overall_score=overall,
            technical_score=tech,
            communication_score=comm,
            duration=str(duration),
        )
        report_dict = report.model_dump(mode="json")

        # Save report to Match table
        with next(get_session()) as db:
            try:
                match = db.exec(
                    select(Match).where(
                        Match.application_id == ctx.state.application.id
                    )
                ).one_or_none()

                if match:
                    match.ai_interview_report = report_dict
                    db.add(match)
                    db.commit()
                    db.refresh(match)
                    logger.info(f"💾 Report saved to Match for application {ctx.state.application.id}")
                else:
                    logger.warning(f"⚠️ No match found for application {ctx.state.application.id}. Report not saved.")

            except Exception as e:
                logger.error(f"❌ Failed to save report to database: {e}")

        logger.info(f"📤 Sending final summary to candidate")

        await ctx.state.ws.send_json({"summary": report_dict})
        await ctx.state.ws.close()
        
        logger.info(f"🔚 Interview session {ctx.state.session_id} completed and closed")
        return End(ctx.state)

live_interview_graph = Graph(
    nodes=[
        AskQuestion, AwaitResponse, ClassifyResponse,
        SendClarification, SendWarning,
        EvaluateAnswer, CheckFollowUp,
        AskFollowUp, NextQuestion, EndInterview
    ]
)

# ───────── FASTAPI APP ─────────
router = APIRouter()
sessions: dict[str, InterviewState] = {}

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Interview Assistant</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      color: #333;
      line-height: 1.6;
    }

    .container {
      max-width: 1000px;
      margin: 0 auto;
      padding: 20px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .header {
      text-align: center;
      margin-bottom: 30px;
      color: white;
    }

    .header h1 {
      font-size: 2.5rem;
      font-weight: 700;
      margin-bottom: 10px;
      text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }

    .header p {
      font-size: 1.1rem;
      opacity: 0.9;
      font-weight: 300;
    }
    
    .chat-container {
      background: white;
      border-radius: 20px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.1);
      overflow: hidden;
      flex: 1;
      display: flex;
      flex-direction: column;
      max-height: 80vh;
    }

    .chat-header {
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: white;
      padding: 20px;
      text-align: center;
    }

    .chat-header h2 {
      font-size: 1.3rem;
      font-weight: 600;
      margin-bottom: 5px;
    }

    .status-indicator {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      opacity: 0.9;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #10b981;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    #chat {
      flex: 1;
      padding: 20px;
      overflow-y: auto;
      background: #f8fafc;
      scrollbar-width: thin;
      scrollbar-color: #cbd5e1 transparent;
    }

    #chat::-webkit-scrollbar {
      width: 6px;
    }

    #chat::-webkit-scrollbar-track {
      background: transparent;
    }

    #chat::-webkit-scrollbar-thumb {
      background: #cbd5e1;
      border-radius: 3px;
    }

    .message {
      margin-bottom: 20px;
      animation: fadeInUp 0.3s ease-out;
    }

    @keyframes fadeInUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .message-content {
      max-width: 80%;
      padding: 15px 20px;
      border-radius: 18px;
      position: relative;
      word-wrap: break-word;
    }

    .bot .message-content {
      background: linear-gradient(135deg, #e0e7ff 0%, #f0f4ff 100%);
      border: 1px solid #c7d2fe;
      margin-right: auto;
      border-bottom-left-radius: 6px;
    }

    .user .message-content {
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: white;
      margin-left: auto;
      border-bottom-right-radius: 6px;
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }

    .message-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-size: 0.85rem;
      opacity: 0.7;
    }

    .bot .message-header {
      color: #4f46e5;
    }

    .user .message-header {
      color: white;
      justify-content: flex-end;
    }

    .evaluation-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      margin: 10px 0;
      box-shadow: 0 4px 12px rgba(0,0,0,0.05);
      border-left: 4px solid #10b981;
    }

    .score-display {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 15px;
    }

    .score-circle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 1.2rem;
      color: white;
    }

    .score-excellent { background: linear-gradient(135deg, #10b981 0%, #059669 100%); }
    .score-good { background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); }
    .score-fair { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); }
    .score-poor { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }

    .feedback-section {
      margin-bottom: 15px;
    }

    .feedback-section h4 {
      color: #374151;
      margin-bottom: 8px;
      font-weight: 600;
      font-size: 0.95rem;
    }

    .feedback-section p, .feedback-section li {
      color: #6b7280;
      font-size: 0.9rem;
      line-height: 1.5;
    }

    .feedback-section ul {
      padding-left: 20px;
    }

    .input-container {
      background: white;
      padding: 20px;
      border-top: 1px solid #e5e7eb;
      display: flex;
      gap: 15px;
      align-items: flex-end;
    }

    #input {
      flex: 1;
      padding: 15px 20px;
      border: 2px solid #e5e7eb;
      border-radius: 25px;
      font-size: 1rem;
      font-family: inherit;
      resize: none;
      min-height: 50px;
      max-height: 120px;
      transition: all 0.2s ease;
      outline: none;
    }

    #input:focus {
      border-color: #4f46e5;
      box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }

    #send {
      background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
      color: white;
      border: none;
      border-radius: 50%;
      width: 50px;
      height: 50px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.2rem;
      transition: all 0.2s ease;
      box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }

    #send:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
    }

    #send:active {
      transform: translateY(0);
    }

    #send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    .typing-indicator {
      display: none;
      align-items: center;
      gap: 8px;
      color: #6b7280;
      font-style: italic;
      padding: 10px 0;
    }

    .typing-dots {
      display: flex;
      gap: 4px;
    }

    .typing-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #9ca3af;
      animation: typing 1.4s infinite ease-in-out;
    }

    .typing-dot:nth-child(1) { animation-delay: 0s; }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }

    @keyframes typing {
      0%, 60%, 100% { transform: translateY(0); }
      30% { transform: translateY(-10px); }
    }

    .final-report {
      background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
      border: 1px solid #0ea5e9;
      border-radius: 16px;
      padding: 25px;
      margin: 15px 0;
    }

    .final-report h3 {
      color: #0c4a6e;
      margin-bottom: 20px;
      font-size: 1.3rem;
      text-align: center;
    }

    .report-stats {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 15px;
      margin-bottom: 20px;
    }

    .stat-item {
      text-align: center;
      padding: 15px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .stat-value {
      font-size: 1.8rem;
      font-weight: 700;
      color: #0c4a6e;
      display: block;
    }

    .stat-label {
      font-size: 0.85rem;
      color: #64748b;
      margin-top: 5px;
    }

    @media (max-width: 768px) {
      .container {
        padding: 10px;
      }

      .header h1 {
        font-size: 2rem;
      }

      .message-content {
        max-width: 90%;
      }

      .input-container {
        padding: 15px;
      }

      .report-stats {
        grid-template-columns: 1fr;
      }
    }

    .loading-screen {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      color: white;
      z-index: 1000;
    }

    .loading-spinner {
      width: 50px;
      height: 50px;
      border: 4px solid rgba(255,255,255,0.3);
      border-top: 4px solid white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
      margin-bottom: 20px;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    .hidden {
      display: none !important;
    }

    .user-info {
      background: rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 15px;
      margin-bottom: 20px;
      color: white;
      text-align: center;
    }

    .user-info .email {
      font-weight: 600;
      font-size: 1.1rem;
    }
  </style>
</head>
<body>
  <div class="loading-screen" id="loadingScreen">
    <div class="loading-spinner"></div>
    <h2>Initializing AI Interview Assistant...</h2>
    <p>Setting up your personalized interview experience</p>
  </div>

  <div class="container" id="interviewContainer">
    <div class="header">
      <h1><i class="fas fa-robot"></i> AI Interview Assistant</h1>
      <div class="user-info">
        <div class="email" id="userEmail"></div>
        <div>Interview in Progress</div>
      </div>
    </div>

    <div class="chat-container">
      <div class="chat-header">
        <h2><i class="fas fa-comments"></i> Interview Session</h2>
        <div class="status-indicator">
          <div class="status-dot"></div>
          <span>Connected & Ready</span>
        </div>
      </div>

      <div id="chat"></div>

      <div class="typing-indicator" id="typingIndicator">
        <i class="fas fa-robot"></i>
        <span>AI is thinking</span>
        <div class="typing-dots">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>

      <div class="input-container">
        <textarea id="input" placeholder="Type your answer here..." rows="1" disabled></textarea>
        <button id="send" title="Send message" disabled>
          <i class="fas fa-paper-plane"></i>
        </button>
      </div>
    </div>
  </div>

<script>
  let ws;
  let isConnected = false;
  let userEmail = '';
  // --- Track copy, paste and tab switches ---
  let pasteCount = 0;
  let tabSwitchCount = 0;
  let copyCount = 0;
  let lastQuestionId = null;

  window.onload = () => {
    const path = window.location.pathname;
    const parts = path.split('/');
    const interviewId = parts[parts.length - 1];

    if (!interviewId || isNaN(parseInt(interviewId))) {
      showError("Invalid interview ID in URL.");
      document.getElementById('loadingScreen').classList.add('hidden');
      return;
    }
    
    connectWebSocket(interviewId);
  };

  async function connectWebSocket(interviewId) {
    try {
      ws = new WebSocket(`${location.protocol === 'http:' ? 'ws' : 'wss'}://${location.host}/api/v1/ai-interviewer/ws/interview/${interviewId}`);
      
      ws.onopen = () => {
        isConnected = true;
        document.getElementById('loadingScreen').classList.add('hidden');
      };
      
      ws.onmessage = handleMessage;
      ws.onclose = handleDisconnect;
      ws.onerror = handleError;
      
    } catch (error) {
      console.error('Connection failed:', error);
      document.getElementById('loadingScreen').classList.add('hidden');
      showError('Failed to connect to the interview system. Please try again.');
    }
  }

  // Auto-resize textarea
  const input = document.getElementById('input');
  input.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
  });

  // Track paste events
  input.addEventListener('paste', function() {
    pasteCount++;
  });

  // Track copy events
  input.addEventListener('copy', function() {
    copyCount++;
  });

  // Track tab switches
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') {
      tabSwitchCount++;
    }
  });

  function resetInteractionCounters() {
    pasteCount = 0;
    tabSwitchCount = 0;
    copyCount = 0;
  }

  function handleMessage(e) {
    hideTypingIndicator();
    const msg = JSON.parse(e.data);
    const chatContainer = document.getElementById('chat');
    
    // Reset counters on new question or followup
    if (msg.question) {
      resetInteractionCounters();
      lastQuestionId = msg.question;
    }
    if (msg.followup_question) {
      resetInteractionCounters();
      lastQuestionId = msg.followup_question;
    }
    if (msg.question) {
      addMessage('bot', `
        <div class="message-header">
          <i class="fas fa-question-circle"></i>
          <span>Interview Question</span>
        </div>
        <strong>Question:</strong> ${msg.question}
      `);
      enableInput();
    } 
    else if (msg.followup_question) {
      addMessage('bot', `
        <div class="message-header">
          <i class="fas fa-search-plus"></i>
          <span>Follow-up Question</span>
        </div>
        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 12px; margin: 8px 0;">
          <div style="color: #92400e; font-size: 0.85rem; margin-bottom: 5px;">
            <i class="fas fa-lightbulb"></i> <strong>Why this follow-up:</strong> ${msg.reason}
          </div>
        </div>
        <strong>Follow-up:</strong> ${msg.followup_question}
      `);
      enableInput();
    }
    else if (msg.evaluation) {
      const overall = msg.evaluation.overall ?? ((msg.evaluation.technical_score + msg.evaluation.communication_score) / 2);
      const scoreClass = getScoreClass(overall);
      addMessage('bot', `
        <div class="evaluation-card">
          <div class="score-display">
            <div class="score-circle ${scoreClass}">
              ${overall.toFixed(1)}
            </div>
            <div>
              <h3>Evaluation Results</h3>
              <p>Your response has been evaluated</p>
            </div>
          </div>
          <div style="display:flex; gap:12px; margin-bottom:12px;">
            <span style="background:#e0f7fa;padding:6px 10px;border-radius:6px; font-size:0.85rem;">Tech: ${msg.evaluation.technical_score}</span>
            <span style="background:#f3e8ff;padding:6px 10px;border-radius:6px; font-size:0.85rem;">Comm: ${msg.evaluation.communication_score}</span>
          </div>
          <div class="feedback-section">
            <h4><i class="fas fa-comment-alt"></i> Feedback</h4>
            <p>${msg.evaluation.feedback}</p>
          </div>
          <div class="feedback-section">
            <h4><i class="fas fa-thumbs-up"></i> Strengths</h4>
            <ul>${msg.evaluation.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
          </div>
          <div class="feedback-section">
            <h4><i class="fas fa-lightbulb"></i> Areas for Improvement</h4>
            <ul>${msg.evaluation.improvements.map(i => `<li>${i}</li>`).join('')}</ul>
          </div>
        </div>
      `);
    }
    else if (msg.clarification) {
      addMessage('bot', `
        <div class="message-header">
          <i class="fas fa-info-circle"></i>
          <span>Clarification</span>
        </div>
        ${msg.clarification}
      `);
      enableInput();
    }
    else if (msg.warning) {
      addMessage('bot', `
        <div class="message-header">
          <i class="fas fa-exclamation-triangle"></i>
          <span>Gentle Reminder</span>
        </div>
        ${msg.warning}
      `);
      enableInput();
    }
    else if (msg.feedback) {
      addMessage('bot', `
        <div class="message-header">
          <i class="fas fa-user-tie"></i>
          <span>Context Summary</span>
        </div>
        <strong>Welcome to your interview!</strong><br><br>
        ${msg.feedback}
      `);
    }
    else if (msg.summary) {
      // Create detailed interaction history
      let interactionHistory = '';
      if (msg.summary.turns && msg.summary.turns.length > 0) {
        interactionHistory = msg.summary.turns.map((turn, index) => {
          let turnHtml = `
            <div style="background: white; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid #4f46e5;">
              <h4 style="color: #4f46e5; margin-bottom: 10px;">Question ${index + 1}</h4>
              <div style="margin-bottom: 10px;">
                <strong>Q:</strong> ${turn.question}
              </div>
              <div style="margin-bottom: 10px;">
                <strong>Your Answer:</strong> ${turn.candidate_answer}
                <span style="color: #6b7280; font-size: 0.85rem;"> (${turn.response_time_seconds.toFixed(1)}s)</span>
              </div>`;
          
          if (turn.followup_question && turn.followup_answer) {
            turnHtml += `
              <div style="background: #fef3c7; border-radius: 6px; padding: 10px; margin: 8px 0;">
                <div style="margin-bottom: 8px;">
                  <strong style="color: #92400e;">Follow-up:</strong> ${turn.followup_question}
                </div>
                <div>
                  <strong style="color: #92400e;">Your Follow-up Answer:</strong> ${turn.followup_answer}
                  <span style="color: #6b7280; font-size: 0.85rem;"> (${turn.followup_response_time_seconds ? turn.followup_response_time_seconds.toFixed(1) : '0'}s)</span>
                </div>
              </div>`;
          }
          
          turnHtml += '</div>';
          return turnHtml;
        }).join('');
      }

      addMessage('bot', `
        <div class="final-report">
          <h3><i class="fas fa-trophy"></i> Interview Complete!</h3>
          <div class="report-stats">
            <div class="stat-item">
              <span class="stat-value">${msg.summary.overall_score.toFixed(1)}</span>
              <div class="stat-label">Overall Score</div>
            </div>
            <div class="stat-item">
              <span class="stat-value">${msg.summary.turns.length}</span>
              <div class="stat-label">Questions Answered</div>
            </div>
            <div class="stat-item">
              <span class="stat-value">${msg.summary.duration}</span>
              <div class="stat-label">Duration</div>
            </div>
          </div>
          
          <div style="margin-top: 20px;">
            <h4 style="color: #0c4a6e; margin-bottom: 15px; text-align: center;">
              <i class="fas fa-history"></i> Complete Interview History
            </h4>
            <div style="max-height: 300px; overflow-y: auto; padding: 10px;">
              ${interactionHistory}
            </div>
          </div>
          
          <p style="text-align: center; color: #64748b; margin-top: 20px;">
            Thank you for completing the interview! Your detailed report has been saved.
          </p>
        </div>
      `);
      disableInput();
    }
    
    scrollToBottom();
  }

  function addMessage(type, content) {
    const chatContainer = document.getElementById('chat');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    chatContainer.appendChild(messageDiv);
  }

  function sendMessage() {
    const input = document.getElementById('input');
    const message = input.value.trim();
    
    if (!message || !isConnected) return;
    
    addMessage('user', `
      <div class="message-header">
        <i class="fas fa-user"></i>
        <span>You</span>
      </div>
      ${message}
    `);
    
    // Send as JSON with interaction metrics
    ws.send(JSON.stringify({
      answer: message,
      paste_count: pasteCount,
      tab_switch_count: tabSwitchCount,
      copy_count: copyCount
    }));
    input.value = '';
    input.style.height = 'auto';
    disableInput();
    showTypingIndicator();
    scrollToBottom();
  }

  function getScoreClass(score) {
    if (score >= 90) return 'score-excellent';
    if (score >= 75) return 'score-good';
    if (score >= 60) return 'score-fair';
    return 'score-poor';
  }

  function showTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'flex';
    scrollToBottom();
  }

  function hideTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'none';
  }

  function enableInput() {
    const input = document.getElementById('input');
    const button = document.getElementById('send');
    input.disabled = false;
    button.disabled = false;
    input.focus();
  }

  function disableInput() {
    const input = document.getElementById('input');
    const button = document.getElementById('send');
    input.disabled = true;
    button.disabled = true;
  }

  function scrollToBottom() {
    const chat = document.getElementById('chat');
    setTimeout(() => {
      chat.scrollTop = chat.scrollHeight;
    }, 100);
  }

  function handleDisconnect() {
    isConnected = false;
    addMessage('bot', `
      <div class="message-header">
        <i class="fas fa-wifi"></i>
        <span>System</span>
      </div>
      <em>Connection closed. Interview session ended.</em>
    `);
    disableInput();
  }

  function handleError(error) {
    console.error('WebSocket error:', error);
    showError('Connection error occurred. Please refresh the page.');
  }

  function showError(message) {
    alert(message);
  }

  // Event listeners
  document.getElementById('send').onclick = sendMessage;
  document.getElementById('input').onkeypress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
</script>
</body>
</html>
"""

@router.get('/interview/{interview_id}', response_class=HTMLResponse)
async def get_interview_page(interview_id: int):
    return HTML_INTERFACE

@router.websocket('/ws/interview/{interview_id}')
async def ws_endpoint(websocket: WebSocket, interview_id: int):
    logger.info(f"🔌 WebSocket connection attempt for interview: {interview_id}")

    try:
        with next(get_session()) as db:
            interview = db.get(Interview, interview_id)
            if not interview:
                logger.error(f"❌ Interview {interview_id} not found - closing WebSocket")
                await websocket.close(code=4404)
                return

            application = db.get(Application, interview.application_id)
            if not application:
                logger.error(f"❌ Application for interview {interview_id} not found - closing WebSocket")
                await websocket.close(code=4404)
                return
            
            job = db.get(Job, application.job_id)
            candidate = db.get(Candidate, application.candidate_id)
            
            if not job or not candidate:
                logger.error(f"❌ Job or Candidate for interview {interview_id} not found - closing WebSocket")
                await websocket.close(code=4404)
                return

            await websocket.accept()
            
            # Prepare questions
            questions = [TailoredQuestion.model_validate(q) for q in job.tailored_questions] if job.tailored_questions else []
            if not questions:
                logger.error(f"❌ No tailored questions found for job {job.id} in interview {interview_id}")
                await websocket.send_json({'error': 'No questions configured for this interview.'})
                await websocket.close()
                return

            # Create context summary
            summary = f"Preparing interview for {candidate.full_name} for the role of {job.title}."
            
            # Extract candidate skills properly from SkillItem objects
            candidate_skills = set()
            if candidate.parsed_resume and hasattr(candidate.parsed_resume, 'skills') and candidate.parsed_resume.skills:
                candidate_skills = {skill.name for skill in candidate.parsed_resume.skills}
            elif candidate.parsed_resume and isinstance(candidate.parsed_resume, dict) and candidate.parsed_resume.get('skills'):
                # Handle case where parsed_resume is stored as dict
                skills_data = candidate.parsed_resume.get('skills', [])
                if isinstance(skills_data, list) and skills_data:
                    if isinstance(skills_data[0], dict):
                        candidate_skills = {skill.get('name', '') for skill in skills_data if skill.get('name')}
                    else:
                        candidate_skills = set(skills_data)  # Fallback for simple string list
            
            job_skills = set(job.skills.get('hard_skills', [])) if job.skills else set()
            matching_skills = list(candidate_skills.intersection(job_skills))

            context = ContextSummary(
                summary=summary,
                matching_skills=matching_skills,
                experience_level=job.experience_level,
                recommended_difficulty=job.seniority_level
            )
            
            state = InterviewState(
                interview=interview,
                job=job,
                candidate=candidate,
                application=application,
                context=context,
                questions=questions,
                ws=websocket
            )
            
            sessions[str(interview_id)] = state
            
            logger.info(f"✅ WebSocket connected for interview {interview_id}")
            logger.info(f"👤 Candidate {candidate.full_name} - Job {job.title}")
            logger.info(f"📊 Session state: {len(state.questions)} questions prepared")

            await websocket.send_json({'feedback': state.context.summary})
            logger.info(f"📤 Sent context summary to candidate: {state.context.summary[:50]}...")

            await live_interview_graph.run(AskQuestion(), state=state)
            logger.info(f"🏁 Interview completed for session {state.session_id}")

    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected for interview {interview_id}")
    except Exception as e:
        logger.error(f"❌ Error during interview {interview_id}: {e}", exc_info=True)
        # Ensure socket is closed on error
        if not websocket.client_state == 'DISCONNECTED':
            await websocket.close(code=1011)
    finally:
        if str(interview_id) in sessions:
            del sessions[str(interview_id)]
            logger.info(f"🧼 Cleaned up session for interview {interview_id}")

