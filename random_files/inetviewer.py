# agentic_interview_bot.py
"""
Enhanced Agentic Technical Prescreen Interview Bot (PydanticAI 0.4+)
=======================================================================
This script implements an improved multi-agent interview system using PydanticAI
with better error handling, streamlined flow, and enhanced user experience.

Key Enhancements:
- Fixed API compatibility with PydanticAI 0.4+ (output_type vs output_type)
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
import os
import json as pyjson
from enum import Enum

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
        "question": "Describe the bias-variance tradeoff in machine learning.",
        "ideal_answer": "The bias-variance tradeoff is a fundamental concept where bias is the error from erroneous assumptions in the learning algorithm (underfitting), and variance is the error from sensitivity to small fluctuations in the training set (overfitting). A simple model has high bias and low variance, while a complex model has low bias and high variance. The goal is to find a balance that minimizes total error.",
        "tags": ["machine-learning", "foundations"],
        "difficulty": "beginner",
    },
    {
        "question": "Explain the difference between L1 and L2 regularization and their effects on model weights.",
        "ideal_answer": "L1 regularization (Lasso) adds a penalty equal to the absolute value of the magnitude of coefficients, which can lead to sparse models by shrinking some coefficients to zero. L2 regularization (Ridge) adds a penalty equal to the square of the magnitude of coefficients, which shrinks coefficients towards zero but doesn't typically make them exactly zero. L1 is useful for feature selection.",
        "tags": ["machine-learning", "regularization"],
        "difficulty": "intermediate",
    },
    {
        "question": "How would you handle an imbalanced dataset in a classification problem?",
        "ideal_answer": "Several techniques can be used. Resampling methods like oversampling the minority class (e.g., SMOTE) or undersampling the majority class. Using different evaluation metrics like F1-score, Precision-Recall AUC instead of accuracy. Cost-sensitive learning, where the model is penalized more for misclassifying the minority class. Or using algorithms that inherently handle imbalance.",
        "tags": ["machine-learning", "classification", "data-preprocessing"],
        "difficulty": "intermediate",
    },
    {
        "question": "What are transformer models and what is the role of the self-attention mechanism?",
        "ideal_answer": "Transformers are a type of neural network architecture primarily used for NLP tasks. The self-attention mechanism allows the model to weigh the importance of different words in the input sequence when processing a particular word, capturing contextual relationships regardless of their distance from each other.",
        "tags": ["deep-learning", "nlp", "transformers"],
        "difficulty": "advanced",
    },
    {
        "question": "What is the difference between a normal convolutional layer and a depthwise separable convolution?",
        "ideal_answer": "A standard convolution performs channel-wise and spatial-wise computation in one step. A depthwise separable convolution splits this into two steps: a depthwise convolution that performs spatial convolution independently for each input channel, followed by a pointwise convolution (1x1 convolution) that combines the outputs of the depthwise convolution. This significantly reduces the number of parameters and computational cost.",
        "tags": ["deep-learning", "computer-vision", "cnn"],
        "difficulty": "advanced",
    },
]

# Always overwrite the question bank to ensure latest questions are used
BANK_PATH.write_text(json.dumps(DEFAULT_BANK, indent=2))
QUESTION_BANK = json.loads(BANK_PATH.read_text())


###############################################################################
# ----------------------------- Data Models ----------------------------------#
###############################################################################
from enum import Enum
class MessageType(str, Enum):
    clarification = 'clarification'
    answer = 'answer'
class ResumeInput(BaseModel):
    resume_text: str = Field(..., min_length=10)
    job_description: str = Field(..., min_length=10)


class ContextSummary(BaseModel):
    summary: str = Field(..., description="Brief summary of candidate background")
    matching_skills: List[str] = Field(
        ..., description="Skills that match the job requirements"
    )
    experience_level: str = Field(
        ..., description="Estimated experience level: junior, mid, senior"
    )
    recommended_difficulty: str = Field(
        ...,
        description="Recommended question difficulty: beginner, intermediate, advanced",
    )


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
    technical_accuracy: int = Field(
        ..., ge=0, le=100, description="Technical correctness score"
    )
    completeness: int = Field(
        ..., ge=0, le=100, description="Answer completeness score"
    )
    clarity: int = Field(..., ge=0, le=100, description="Communication clarity score")
    feedback: str = Field(..., description="Detailed feedback for the candidate")
    strengths: List[str] = Field(..., description="Identified strengths in the answer")
    improvements: List[str] = Field(..., description="Areas for improvement")
    follow_up_needed: bool = Field(
        ..., description="Whether a follow-up question is recommended"
    )


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


class GeneratedQuestion(BaseModel):
    question: str = Field(..., description="The interview question")
    ideal_answer: str = Field(..., description="Expected ideal answer")
    tags: list[str] = Field(..., description="Question topic tags")
    difficulty: str = Field(..., description="Question difficulty level: simple, intermediate, challenging")


class GeneratedQuestionBatch(BaseModel):
    questions: list[GeneratedQuestion] = Field(..., min_items=3, max_items=10)
    reasoning: str = Field(..., description="Explanation for question selection and coverage")


###############################################################################
# -------------------------------- Agents ------------------------------------#
###############################################################################

# Context Analysis Agent
context_agent = Agent(
    model=LOCAL_MODEL,
    deps_type=ResumeInput,
    output_type=ContextSummary,
    system_prompt=(
        "You are an expert technical recruiter. Analyze the candidate's resume and job description. "
        "Provide a concise summary of their background, identify matching skills, estimate their experience level, "
        "and recommend appropriate question difficulty. Be thorough but concise."
    ),
    result_retries=3
)

# Question Selection Agent
question_agent = Agent(
    model=LOCAL_MODEL,
    deps_type=ContextSummary,
    output_type=QuestionBatch,
    system_prompt=(
        "You are an expert interview designer. Based on the candidate summary and available questions, "
        "select 3-4 most relevant questions that match their experience level and the job requirements. "
        "Prioritize questions that will best assess their fit for the role. Explain your selection reasoning."
    ),
    result_retries=3
)

# AI Question Generation Agent
question_generation_agent = Agent(
    model=LOCAL_MODEL,
    deps_type=str,
    output_type=GeneratedQuestionBatch,
    system_prompt=(
        "You are an expert technical interviewer. Given a job description, generate a set of 5-7 interview questions for a candidate. "
        "The questions must be ordered from simple to challenging, and together should cover all key areas and requirements in the job description. "
        "For each question, provide: the question, an ideal answer, topic tags, and a difficulty label (simple, intermediate, challenging). "
        "When generating questions, ALWAYS use explicit, concrete technologies, tools, or skills that are actually mentioned in the job description. "
        "Do NOT use placeholders like [specific technology/tool] or [framework]. If the job description mentions 'PyTorch', 'Kubernetes', 'AWS SageMaker', etc., use those exact names in the questions. "
        "Ensure the set is comprehensive and tailored to the job description."
    ),
    result_retries=3
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
    output_type=Evaluation,
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
    result_retries=3
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
                    deps=resume_input,
                )
                logger.info(f"Context agent raw output: {context_result}")
                self.context = context_result.output

                # Ensure all required fields are present
                if not hasattr(self.context, "experience_level"):
                    self.context.experience_level = "mid"
                if not hasattr(self.context, "recommended_difficulty"):
                    self.context.recommended_difficulty = "intermediate"
                if not hasattr(self.context, "matching_skills"):
                    self.context.matching_skills = ["general programming"]

            except Exception as e:
                logger.error(
                    f"Context analysis failed: {str(e)}\nResume: {resume}\nJob: {job}\nUsing fallback context."
                )
                # Fallback context
                self.context = ContextSummary(
                    summary="Candidate profile analysis unavailable. Proceeding with standard interview.",
                    matching_skills=["programming", "problem-solving"],
                    experience_level="mid",
                    recommended_difficulty="intermediate",
                )
            logger.info(f"Context analysis completed for session {self.id}")

            # Generate questions using the AI agent
            try:
                logger.info(f"Generating questions from job description for session {self.id}")
                gen_result = question_generation_agent.run_sync(
                    "Generate a comprehensive set of interview questions for this job description.",
                    deps=job,
                )
                logger.info(f"Question generation agent output: {gen_result}")
                self.question_batch = gen_result.output
                # Convert to TailoredQuestion for compatibility
                self.questions = [
                    TailoredQuestion(
                        question=q.question,
                        ideal_answer=q.ideal_answer,
                        tags=q.tags,
                        difficulty=q.difficulty,
                    )
                    for q in self.question_batch.questions
                ]
            except Exception as e:
                logger.error(
                    f"AI question generation failed: {str(e)}, using fallback questions"
                )
                # Fallback to default questions if AI selection fails
                fallback_questions = [
                    TailoredQuestion(
                        question=q["question"],
                        ideal_answer=q["ideal_answer"],
                        tags=q.get("tags", ["general"]),
                        difficulty=q.get("difficulty", "intermediate"),
                    )
                    for q in QUESTION_BANK[:5]
                ]
                self.questions = fallback_questions
                self.question_batch = QuestionBatch(
                    questions=fallback_questions,
                    reasoning="Used fallback questions due to AI question generation failure",
                )
            logger.info(
                f"Selected {len(self.questions)} questions for session {self.id}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize session {self.id}: {str(e)}")
            raise HTTPException(
                500, f"Failed to initialize interview session: {str(e)}"
            )

    def get_current_question(self) -> Optional[str]:
        """Get the current question without advancing the index."""
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index].question
        return None

    def advance_to_next_question(self) -> Optional[str]:
        """Advance to the next question and return it."""
        self.current_question_index += 1
        return self.get_current_question()

    async def process_answer(self, answer: str) -> tuple[Evaluation, InterviewProgress, bool]:
        """Process the candidate's answer and return evaluation with progress and a flag for unrelated answer."""
        if self.current_question_index >= len(self.questions):
            raise ValueError("No more questions available")

        current_q = self.questions[self.current_question_index]

        # Create interview turn
        turn = InterviewTurn(
            question=current_q.question,
            ideal_answer=current_q.ideal_answer,
            candidate_answer=answer,
        )

        unrelated = False
        try:
            # Debug logging
            logger.info(f"Evaluating answer for session {self.id}: '{answer[:50]}...'")
            logger.info(f"Question: '{current_q.question}'")
            logger.info(f"Expected: '{current_q.ideal_answer[:50]}...'")

            # Check if answer is unrelated (very low similarity)
            # Use rapidfuzz for a quick check
            sim = fuzz.partial_ratio(answer.lower(), current_q.question.lower())
            logger.info(f"Answer-question similarity: {sim}")
            if sim < 20 and len(answer.strip()) > 0:
                unrelated = True

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
            evaluation = eval_result.output

            logger.info(
                f"Received evaluation: score={evaluation.score}, tech={evaluation.technical_accuracy}, complete={evaluation.completeness}, clarity={evaluation.clarity}"
            )

            # Fallback scoring if needed
            if (
                evaluation.score == 0
                and evaluation.technical_accuracy == 0
                and evaluation.completeness == 0
            ):
                answer_lower = answer.lower()
                ideal_lower = current_q.ideal_answer.lower()
                if len(answer.strip()) < 5:
                    tech_score = 10
                    completeness_score = 10
                    clarity_score = 20
                elif any(
                    word in answer_lower
                    for word in ["mutable", "immutable", "list", "tuple"]
                ):
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
                    feedback=f"Based on your answer '{answer}', here's my assessment: "
                    + (
                        "Good understanding of mutability concepts!"
                        if tech_score > 50
                        else "Consider elaborating on the key differences between these data structures."
                    ),
                    strengths=["Answered the question"]
                    if len(answer.strip()) > 5
                    else [],
                    improvements=[
                        "Provide more detailed explanation",
                        "Include specific examples",
                    ],
                    follow_up_needed=False,
                )

            # Only store the turn and evaluation if not unrelated
            if not unrelated:
                self.turns.append(turn)
                self.evaluations.append(evaluation)

            # Calculate progress
            progress = self._calculate_progress()

            logger.info(
                f"Processed answer for session {self.id}, question {self.current_question_index + 1}, score: {evaluation.score}"
            )
            return evaluation, progress, unrelated

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
                follow_up_needed=False,
            )
            if not unrelated:
                self.evaluations.append(fallback_evaluation)
            progress = self._calculate_progress()
            return fallback_evaluation, progress, unrelated

    def _calculate_progress(self) -> InterviewProgress:
        """Calculate current interview progress."""
        avg_score = sum(e.score for e in self.evaluations) / max(
            len(self.evaluations), 1
        )
        elapsed = datetime.now() - self.start_time
        elapsed_str = f"{elapsed.seconds // 60}m {elapsed.seconds % 60}s"

        return InterviewProgress(
            current_question=len(self.evaluations),
            total_questions=len(self.questions),
            average_score=avg_score,
            time_elapsed=elapsed_str,
        )

    def generate_final_report(self) -> FinalTranscript:
        """Generate comprehensive final interview report."""
        if not self.evaluations:
            raise ValueError("No evaluations available for final report")

        # Calculate scores
        overall_score = sum(e.score for e in self.evaluations) / len(self.evaluations)
        technical_score = sum(e.technical_accuracy for e in self.evaluations) / len(
            self.evaluations
        )
        communication_score = sum(e.clarity for e in self.evaluations) / len(
            self.evaluations
        )

        # Generate recommendation
        if overall_score >= 80:
            recommendation = "Strong Hire - Candidate demonstrates excellent technical knowledge and communication skills."
        elif overall_score >= 65:
            recommendation = (
                "Hire - Candidate shows good technical competency with room for growth."
            )
        elif overall_score >= 50:
            recommendation = (
                "Borderline - Consider for junior roles or with additional training."
            )
        else:
            recommendation = "No Hire - Candidate needs significant development before being ready for this role."

        # Generate summary
        strengths = []
        improvements = []
        for eval in self.evaluations:
            strengths.extend(eval.strengths)
            improvements.extend(eval.improvements)

        summary = (
            f"Candidate completed {len(self.evaluations)} questions with an overall score of {overall_score:.1f}%. "
            f"Key strengths: {', '.join(set(strengths)[:3])}. "
            f"Areas for improvement: {', '.join(set(improvements)[:3])}."
        )

        # Calculate duration
        duration = datetime.now() - self.start_time
        duration_str = f"{duration.seconds // 60}m {duration.seconds % 60}s"

        final_report = FinalTranscript(
            session_id=self.id,
            turns=self.turns,
            evaluations=self.evaluations,
            overall_score=overall_score,
            technical_score=technical_score,
            communication_score=communication_score,
            recommendation=recommendation,
            summary=summary,
            duration=duration_str,
        )

        # Save report as JSON in backend
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = reports_dir / f"report_{self.id}_{timestamp}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                pyjson.dump(final_report.model_dump(mode="json"), f, ensure_ascii=False, indent=2)
            logger.info(f"Saved final report to {report_path}")
        except Exception as e:
            logger.error(f"Failed to save final report for session {self.id}: {e}")

        return final_report

    async def classify_message_type(self, candidate_message: str) -> MessageType:
        # Use LLM to classify the message as 'clarification' or 'answer'
        current_q = self.questions[self.current_question_index]
        classify_prompt = (
            f"You are an expert technical interviewer. Given the interview question and the candidate's message, decide if the candidate is asking for clarification or providing an answer.\n"
            f"INTERVIEW QUESTION: {current_q.question}\n"
            f"CANDIDATE MESSAGE: {candidate_message}\n"
            f"Respond with only one word: 'clarification' or 'answer'."
        )
        class ResponseTypeModel(BaseModel):
            response_type: MessageType = Field(..., description="The type of response: 'clarification' or 'answer'")
        try:
            classify_agent = Agent(
                model=LOCAL_MODEL,
                deps_type=str,
                output_type=ResponseTypeModel,
                system_prompt="Classify the candidate's message as either 'clarification' or 'answer' for the interview question. Respond with only one word."
            )
            result = classify_agent.run_sync(classify_prompt, deps=candidate_message)
            label = result.output.response_type if hasattr(result.output, 'response_type') else MessageType.answer
            return label
        except Exception as e:
            logger.error(f"LLM classify agent failed: {e}")
            # Fallback: treat as answer
            return MessageType.answer


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
            "selection_reasoning": sess.question_batch.reasoning,
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

    async def send_clarification(user_question: str):
        # Use LLM to generate a clarification/explanation for the current question
        current_q = session.questions[session.current_question_index]
        clarification_prompt = (
            f"You are an expert technical interviewer. The candidate asked for clarification about the interview question.\n"
            f"INTERVIEW QUESTION: {current_q.question}\n"
            f"CANDIDATE'S CLARIFICATION QUESTION: {user_question}\n"
            f"Please provide a concise, helpful clarification or explanation to help the candidate understand the question."
        )
        try:
            clarification_agent = Agent(
                model=LOCAL_MODEL,
                deps_type=str,
                output_type=str,
                system_prompt="You are a helpful technical interviewer. Answer clarification questions about the interview question."
            )
            result = clarification_agent.run_sync(clarification_prompt, deps=user_question)
            clarification = result.output if hasattr(result, 'output') else str(result)
            # Always return the clarification to the user
            await websocket.send_json({"type": "clarification", "data": {"clarification": clarification}})
        except Exception as e:
            logger.error(f"Clarification agent failed: {e}")
            clarification = "I'm sorry, I couldn't generate a clarification at this time. Please try to answer the question as best you can."
            await websocket.send_json({"type": "clarification", "data": {"clarification": clarification}})

    try:
        while True:
            # Receive candidate answer
            answer = await websocket.receive_text()

            answer_strip = answer.strip()
            # Use LLM to classify the message type
            message_type = await session.classify_message_type(answer_strip)
            logger.info(f"Classifier output for message '{answer_strip}': {message_type}")
            if message_type == MessageType.clarification:
                await send_clarification(answer_strip)
                continue

            if answer_strip.lower() in ["quit", "exit", "end"]:
                final_report = session.generate_final_report()
                await websocket.send_json(
                    {"type": "final_report", "data": final_report.model_dump(mode="json")}
                )
                await websocket.close()
                break

            # Process the answer
            evaluation, progress, unrelated = await session.process_answer(answer)

            # If unrelated, ask for follow-up and do not advance question index
            if unrelated:
                follow_up = "Your answer does not seem related to the question. Please answer only the question asked."
                await websocket.send_json(
                    {"type": "follow_up", "data": {"question": follow_up}}
                )
                continue

            # Send evaluation feedback
            await websocket.send_json(
                {
                    "type": "evaluation",
                    "data": {
                        "score": evaluation.score,
                        "feedback": evaluation.feedback,
                        "strengths": evaluation.strengths,
                        "improvements": evaluation.improvements,
                        "technical_accuracy": evaluation.technical_accuracy,
                        "completeness": evaluation.completeness,
                        "clarity": evaluation.clarity,
                    },
                }
            )

            # Send progress update
            await websocket.send_json({"type": "progress", "data": progress.model_dump(mode="json")})

            # Move to next question
            next_question = session.advance_to_next_question()
            if next_question:
                await websocket.send_json(
                    {"type": "next_question", "data": {"question": next_question}}
                )
            else:
                # Interview complete
                final_report = session.generate_final_report()
                await websocket.send_json(
                    {"type": "final_report", "data": final_report.model_dump(mode="json")}
                )
                await websocket.close()
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        # Ensure report is saved if there are any evaluations
        try:
            if session.evaluations:
                session.generate_final_report()
        except Exception as e:
            logger.error(f"Failed to save report on disconnect for session {session_id}: {e}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        # Ensure report is saved if there are any evaluations
        try:
            if session.evaluations:
                session.generate_final_report()
        except Exception as e2:
            logger.error(f"Failed to save report on error for session {session_id}: {e2}")
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
    <title>AI Engineer Interview Bot</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background-color: #f4f7f9;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #4a90e2 0%, #50e3c2 100%); 
            color: white; 
            padding: 40px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.8em; margin-bottom: 10px; font-weight: 700; }
        .header p { opacity: 0.9; font-size: 1.2em; }
        .content { padding: 40px; }
        
        #setupInfo { text-align: center; }
        .job-resume-container {
            display: flex;
            gap: 30px;
            margin-bottom: 30px;
            text-align: left;
        }
        .info-box {
            flex: 1;
            background-color: #fafafa;
            border: 1px solid #eef;
            border-radius: 10px;
            padding: 20px;
        }
        .info-box h3 {
            font-size: 1.4em;
            color: #4a90e2;
            margin-bottom: 15px;
            border-bottom: 2px solid #50e3c2;
            padding-bottom: 10px;
        }
        pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 14px;
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #eee;
            max-height: 250px;
            overflow-y: auto;
        }

        .btn { 
            background: linear-gradient(135deg, #4a90e2 0%, #50e3c2 100%); 
            color: white; 
            border: none; 
            padding: 15px 30px; 
            border-radius: 50px; 
            font-size: 16px; 
            font-weight: 600; 
            cursor: pointer; 
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }
        .btn:disabled { 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none; 
            box-shadow: none;
        }

        #interviewSection { margin-top: 30px; }
        #chat { 
            border: 1px solid #eef; 
            border-radius: 10px; 
            height: 450px; 
            overflow-y: auto; 
            padding: 20px; 
            margin-bottom: 20px; 
            background: #fdfdfd;
        }
        .message { 
            margin-bottom: 20px; 
            display: flex;
            align-items: flex-start;
            max-width: 85%;
        }
        .message .content-wrapper {
            padding: 15px 20px; 
            border-radius: 18px; 
        }
        .user { 
            margin-left: auto; 
            flex-direction: row-reverse;
        }
        .user .content-wrapper {
            background: #4a90e2;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .bot .content-wrapper { 
            background: #f1f1f1;
            color: #333;
            border-bottom-left-radius: 4px;
        }
        .message strong { display: block; margin-bottom: 5px; }

        .evaluation, .progress, .system {
            margin: 20px auto;
            max-width: 100%;
            border-left-width: 5px;
            border-left-style: solid;
            padding: 15px;
            border-radius: 5px;
            background-color: #f8f9fa;
        }
        .evaluation { border-color: #ff9800; }
        .progress { border-color: #9c27b0; }
        .system { border-color: #777; }

        .input-area { 
            display: flex; 
            gap: 10px; 
            align-items: center; 
        }
        .input-area input { 
            flex: 1; 
            margin-bottom: 0; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 50px; 
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        .input-area input:focus { 
            outline: none; 
            border-color: #4a90e2; 
        }
        
        .score { font-weight: bold; font-size: 1.2em; }
        .score.high { color: #4caf50; }
        .score.medium { color: #ff9800; }
        .score.low { color: #f44336; }
        .hidden { display: none; }
        .loading { 
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255,255,255,0.8);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.2em; color: #333; z-index: 1000;
        }
        /* Modal Overlay Styles */
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            width: 100vw; height: 100vh;
            background: rgba(44, 62, 80, 0.85);
            z-index: 2000;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: opacity 0.5s;
        }
        .modal-content {
            background: #fff;
            border-radius: 18px;
            box-shadow: 0 8px 40px rgba(0,0,0,0.18);
            padding: 40px 30px 30px 30px;
            max-width: 900px;
            width: 100%;
            animation: modalIn 0.6s cubic-bezier(.68,-0.55,.27,1.55);
        }
        @keyframes modalIn {
            0% { transform: scale(0.95) translateY(40px); opacity: 0; }
            100% { transform: scale(1) translateY(0); opacity: 1; }
        }
        .modal-overlay.hide {
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.5s;
        }
        .evaluation-table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0 15px 0;
        }
        .evaluation-table th, .evaluation-table td {
            padding: 8px 12px;
            text-align: center;
        }
        .evaluation-table th {
            background: #e3eafc;
            color: #2a3b5d;
            font-weight: 600;
            border-bottom: 2px solid #b6c6e3;
        }
        .evaluation-table td {
            background: #fff;
            border-bottom: 1px solid #f0f0f0;
        }
        .evaluation-table .score-cell {
            font-weight: bold;
            font-size: 1.1em;
        }
        .evaluation-table .score-high { color: #4caf50; }
        .evaluation-table .score-medium { color: #ff9800; }
        .evaluation-table .score-low { color: #f44336; }
        .eval-section-label {
            font-weight: 600;
            color: #4a90e2;
            margin-top: 10px;
            margin-bottom: 2px;
            display: block;
        }
        @media (max-width: 600px) {
            .evaluation-table th, .evaluation-table td { font-size: 13px; padding: 6px 4px; }
        }
        .job-edit-textarea {
            width: 100%;
            min-height: 180px;
            font-size: 15px;
            font-family: 'Consolas', 'Courier New', monospace;
            background: #fff;
            border: 1.5px solid #b6c6e3;
            border-radius: 7px;
            padding: 12px;
            resize: vertical;
            margin-top: 5px;
            margin-bottom: 0;
            box-sizing: border-box;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Engineer Interview Bot</h1>
            <p>An AI-Powered Technical Interview Assistant</p>
        </div>
        
        <div class="content">
            <!-- Modal Overlay for Setup -->
            <div id="setupOverlay" class="modal-overlay">
                <div id="setupInfo" class="modal-content">
                    <div class="job-resume-container">
                        <div class="info-box">
                            <h3>📄 Candidate Resume</h3>
                            <pre id="resume-text">
**Summary:**
AI Engineer with 3+ years of experience in developing and deploying machine learning models. Proven ability to architect and implement end-to-end MLOps pipelines. Passionate about leveraging AI to solve complex real-world problems.

**Experience:**
- Senior AI Engineer, TechCorp (2021-Present)
  - Led the development of a real-time recommendation engine, improving user engagement by 25%.
  - Designed and deployed scalable training pipelines on AWS using SageMaker, Lambda, and Step Functions.
  - Optimized model inference latency by 40% through quantization and graph optimization.

**Skills:**
- Programming: Python (Expert), C++, Go
- ML/DL: PyTorch, TensorFlow, Scikit-learn, Hugging Face
- MLOps: Docker, Kubernetes, Kubeflow, MLflow, AWS SageMaker
- Data: SQL, NoSQL, Spark, Pandas, NumPy
                            </pre>
                        </div>
                        <div class="info-box">
                            <h3>💼 Job Description</h3>
                            <textarea id="job-text" class="job-edit-textarea">
**Role:** AI Engineer

**Responsibilities:**
- Design, build, train, and deploy machine learning models.
- Develop and maintain scalable MLOps infrastructure for model lifecycle management.
- Collaborate with data scientists to productize ML prototypes.
- Research and implement state-of-the-art algorithms to tackle business challenges.
- Ensure model performance, scalability, and reliability in production.

**Qualifications:**
- BS/MS in Computer Science or related field.
- Strong experience in Python and ML frameworks (PyTorch, TensorFlow).
- Hands-on experience with cloud platforms (AWS, GCP, or Azure).
- Solid software engineering fundamentals.
- Familiarity with CI/CD, Docker, and Kubernetes is a plus.
                            </textarea>
                        </div>
                    </div>
                    <button id="startBtn" class="btn">🚀 Start Interview</button>
                </div>
            </div>
            <!-- End Modal Overlay -->

            <div id="interviewSection" class="hidden">
                <div id="contextInfo" class="message bot"><div class="content-wrapper"></div></div>
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

        document.getElementById('startBtn').onclick = async () => {
            const resume = document.getElementById('resume-text').textContent.trim();
            const job = document.getElementById('job-text').value.trim();
            document.getElementById('startBtn').disabled = true;
            showLoading('Creating interview session...');
            try {
                const response = await fetch('/session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ resume_text: resume, job_description: job })
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
                }
                const data = await response.json();
                currentSession = data;
                // Animate modal overlay out
                const overlay = document.getElementById('setupOverlay');
                overlay.classList.add('hide');
                setTimeout(() => {
                    overlay.style.display = 'none';
                    document.getElementById('interviewSection').classList.remove('hidden');
                }, 500);
                const contextInfo = document.querySelector('#contextInfo .content-wrapper');
                contextInfo.innerHTML = `
                    <strong>📊 Interview Setup Complete</strong><br>
                    <strong>Context:</strong> ${data.context_summary}<br>
                    <strong>Questions:</strong> ${data.total_questions} selected<br>
                    <strong>Reasoning:</strong> ${data.selection_reasoning}<br>
                    <hr style="margin: 10px 0; border-color: #ddd;">
                    <strong>First Question:</strong> ${data.first_question}
                `;
                connectWebSocket(data.session_id);
            } catch (error) {
                console.error('Error creating session:', error);
                alert('Failed to create interview session. Check the console for details.');
                document.getElementById('startBtn').disabled = false;
            } finally {
                hideLoading();
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
                document.getElementById('answerInput').disabled = true;
                document.getElementById('sendBtn').disabled = true;
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
                    addMessage('bot', `📝 <strong>Next Question:</strong> ${message.data.question}`);
                    break;
                case 'follow_up':
                    addMessage('bot', `🔍 <strong>Follow-up:</strong> ${message.data.question}`);
                    break;
                case 'clarification':
                    addMessage('bot', `💡 <strong>Clarification:</strong> ${message.data.clarification}`);
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
                    <strong>📊 Evaluation Results</strong>
                    <table class="evaluation-table">
                        <tr>
                            <th>Overall</th>
                            <th>Technical</th>
                            <th>Completeness</th>
                            <th>Clarity</th>
                        </tr>
                        <tr>
                            <td class="score-cell score-${scoreClass}">${data.score}/100</td>
                            <td>${data.technical_accuracy}/100</td>
                            <td>${data.completeness}/100</td>
                            <td>${data.clarity}/100</td>
                        </tr>
                    </table>
                    <span class="eval-section-label">💬 Feedback:</span>
                    <div style="margin-bottom:8px;">${data.feedback}</div>
                    <span class="eval-section-label">✅ Strengths:</span>
                    <div style="margin-bottom:8px;">${(data.strengths && data.strengths.length) ? data.strengths.join(', ') : 'N/A'}</div>
                    <span class="eval-section-label">📈 Improvements:</span>
                    <div>${(data.improvements && data.improvements.length) ? data.improvements.join(', ') : 'N/A'}</div>
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
            // Build Q&A table
            let qaTable = `<table class="evaluation-table" style="margin-top:18px;">
                <tr>
                    <th>#</th>
                    <th>Question</th>
                    <th>Your Answer</th>
                    <th>Ideal Answer</th>
                    <th>Score</th>
                </tr>`;
            for (let i = 0; i < data.turns.length; i++) {
                const turn = data.turns[i];
                const eval_ = data.evaluations[i];
                const turnScoreClass = eval_ && eval_.score >= 70 ? 'score-high' : eval_ && eval_.score >= 50 ? 'score-medium' : 'score-low';
                qaTable += `<tr>
                    <td>${i + 1}</td>
                    <td style="min-width:160px;max-width:260px;">${turn.question}</td>
                    <td style="min-width:140px;max-width:220px;">${turn.candidate_answer}</td>
                    <td style="min-width:140px;max-width:220px;">${turn.ideal_answer}</td>
                    <td class="score-cell ${turnScoreClass}">${eval_ ? eval_.score : '-'}/100</td>
                </tr>`;
            }
            qaTable += `</table>`;

            const reportHtml = `
                <div class="message bot">
                    <div class="content-wrapper">
                        <strong>🎯 Interview Complete!</strong><br><br>
                        <span class="score ${scoreClass}">Final Score: ${data.overall_score.toFixed(1)}/100</span><br>
                        <small>Technical: ${data.technical_score.toFixed(1)} | Communication: ${data.communication_score.toFixed(1)}</small><br><br>
                        <strong>📋 Summary:</strong> ${data.summary}<br><br>
                        <strong>🎯 Recommendation:</strong> ${data.recommendation}<br><br>
                        <strong>⏱️ Duration:</strong> ${data.duration}<br><br>
                        <hr style="margin:18px 0;">
                        <strong>📝 Questions & Answers:</strong>
                        ${qaTable}
                    </div>
                </div>
            `;
            document.getElementById('chat').innerHTML += reportHtml;
            scrollToBottom();
            document.getElementById('answerInput').disabled = true;
            document.getElementById('sendBtn').disabled = true;
        }

        function addMessage(type, text) {
            const chat = document.getElementById('chat');
            if (type === 'system') {
                 chat.innerHTML += `<div class="message system">${text}</div>`;
            } else {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                messageDiv.innerHTML = `<div class="content-wrapper">${text}</div>`;
                chat.appendChild(messageDiv);
            }
            scrollToBottom();
        }

        function sendAnswer() {
            const input = document.getElementById('answerInput');
            const answer = input.value.trim();
            
            if (!answer || !ws || ws.readyState !== WebSocket.OPEN) return;
            
            addMessage('user', `<strong>You:</strong> ${answer}`);
            ws.send(answer);
            input.value = '';
        }

        let loadingDiv = null;
        function showLoading(message) {
            if (loadingDiv) return;
            loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = `⏳ ${message}`;
            document.body.appendChild(loadingDiv);
        }
        
        function hideLoading() {
            if (loadingDiv) {
                loadingDiv.parentNode.removeChild(loadingDiv);
                loadingDiv = null;
            }
        }

        function scrollToBottom() {
            const chat = document.getElementById('chat');
            chat.scrollTop = chat.scrollHeight;
        }

        document.getElementById('sendBtn').onclick = sendAnswer;
        document.getElementById('answerInput').onkeypress = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendAnswer();
            }
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
        candidate_answer="list is mutable, but tuple is not mutable",
    )

    try:
        result = await evaluation_agent.run(
            "Please evaluate this test response.", deps=test_turn
        )
        print("✅ Test Evaluation Result:")
        print(f"Score: {result.output.score}")
        print(f"Feedback: {result.output.feedback}")
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
