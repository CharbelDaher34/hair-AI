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

# Adaptive Question Pools
STRETCH_QUESTIONS = [
    {
        "question": "Design a distributed machine learning system that can handle model training across multiple data centers with network partitions. How would you ensure consistency and fault tolerance?",
        "ideal_answer": "A distributed ML system needs consensus protocols like Raft for coordination, parameter servers or federated learning for distributed training, checkpointing for fault recovery, and techniques like asynchronous SGD or model averaging to handle network partitions. Key considerations include data locality, communication overhead, and handling stragglers.",
        "tags": ["distributed-systems", "machine-learning", "system-design"],
        "difficulty": "challenging",
        "rubric": {
            "points": [
                {"criterion": "Distributed Architecture", "weight": 0.3, "description": "Understanding of distributed system components"},
                {"criterion": "Fault Tolerance", "weight": 0.3, "description": "Strategies for handling failures and network partitions"},
                {"criterion": "ML-Specific Considerations", "weight": 0.4, "description": "Understanding of distributed training challenges"}
            ]
        }
    },
    {
        "question": "Explain how you would implement a real-time recommendation system that can handle 1M+ requests per second with sub-100ms latency while continuously learning from user interactions.",
        "ideal_answer": "Requires a multi-tier architecture with edge caching, feature stores, online/offline learning pipeline, A/B testing framework, and techniques like approximate nearest neighbors, model quantization, and streaming ML. Key is separating inference from training and using techniques like negative sampling and incremental learning.",
        "tags": ["system-design", "machine-learning", "scalability"],
        "difficulty": "challenging",
        "rubric": {
            "points": [
                {"criterion": "System Architecture", "weight": 0.25, "description": "High-level system design for scale"},
                {"criterion": "Latency Optimization", "weight": 0.25, "description": "Techniques to achieve sub-100ms response"},
                {"criterion": "Online Learning", "weight": 0.25, "description": "Continuous learning from user interactions"},
                {"criterion": "Scalability Considerations", "weight": 0.25, "description": "Handling 1M+ QPS requirements"}
            ]
        }
    }
]

DIAGNOSTIC_QUESTIONS = [
    {
        "question": "What is overfitting in machine learning and how can you detect it?",
        "ideal_answer": "Overfitting occurs when a model learns the training data too well, including noise and irrelevant patterns, leading to poor generalization. It can be detected by monitoring training vs validation loss curves - overfitting shows when training loss continues decreasing while validation loss increases. Prevention methods include regularization, cross-validation, and early stopping.",
        "tags": ["machine-learning", "fundamentals"],
        "difficulty": "simple",
        "rubric": {
            "points": [
                {"criterion": "Definition Understanding", "weight": 0.4, "description": "Clear explanation of what overfitting means"},
                {"criterion": "Detection Methods", "weight": 0.3, "description": "How to identify overfitting in practice"},
                {"criterion": "Prevention Strategies", "weight": 0.3, "description": "Techniques to prevent overfitting"}
            ]
        }
    },
    {
        "question": "Explain the difference between supervised and unsupervised learning with examples.",
        "ideal_answer": "Supervised learning uses labeled training data to learn a mapping from inputs to outputs (e.g., classification, regression). Examples include email spam detection, image recognition. Unsupervised learning finds patterns in data without labels (e.g., clustering, dimensionality reduction). Examples include customer segmentation, anomaly detection.",
        "tags": ["machine-learning", "fundamentals"],
        "difficulty": "simple",
        "rubric": {
            "points": [
                {"criterion": "Supervised Learning", "weight": 0.4, "description": "Understanding of supervised learning concept"},
                {"criterion": "Unsupervised Learning", "weight": 0.4, "description": "Understanding of unsupervised learning concept"},
                {"criterion": "Examples", "weight": 0.2, "description": "Relevant examples for both types"}
            ]
        }
    }
]

###############################################################################
# ----------------------------- Data Models ----------------------------------#
###############################################################################
class MessageType(str, Enum):
    clarification = 'clarification'
    answer = 'answer'
    unrelated = 'unrelated'

class DifficultyLevel(str, Enum):
    simple = 'simple'
    intermediate = 'intermediate'
    challenging = 'challenging'

class RubricPoint(BaseModel):
    criterion: str = Field(..., description="What is being evaluated")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight of this criterion (0-1)")
    description: str = Field(..., description="Description of what constitutes a good answer for this criterion")

class QuestionRubric(BaseModel):
    points: List[RubricPoint] = Field(..., description="List of evaluation criteria")
    total_possible_score: int = Field(default=100, description="Maximum possible score")

class ResumeInput(BaseModel):
    resume_text: str = Field(..., min_length=10)
    job_description: str = Field(..., min_length=10)
    questions: Optional[List[str]] = None
    answers: Optional[List[str]] = None


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
    rubric: Optional[QuestionRubric] = Field(None, description="Structured evaluation rubric")


class QuestionBatch(BaseModel):
    questions: List[TailoredQuestion] = Field(..., min_items=1, max_items=5)
    reasoning: str = Field(..., description="Explanation for question selection")


class InterviewTurn(BaseModel):
    question: str = Field(..., description="The question asked")
    ideal_answer: str = Field(..., description="The expected answer")
    candidate_answer: str = Field(..., description="The candidate's response")
    timestamp: datetime = Field(default_factory=datetime.now)
    response_time_seconds: Optional[float] = Field(None, description="Time taken to respond in seconds")
    clarification_count: int = Field(default=0, description="Number of clarifications requested for this question")


class RubricScore(BaseModel):
    criterion: str = Field(..., description="The evaluation criterion")
    score: int = Field(..., ge=0, le=100, description="Score for this criterion")
    feedback: str = Field(..., description="Specific feedback for this criterion")


class Evaluation(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Score out of 100")
    technical_accuracy: int = Field(
        ..., ge=0, le=100, description="Technical correctness score"
    )
    completeness: int = Field(
        ..., ge=0, le=100, description="Answer completeness score"
    )
    clarity: int = Field(..., ge=0, le=100, description="Communication clarity score")
    rubric_scores: List[RubricScore] = Field(default_factory=list, description="Detailed rubric-based scores")
    feedback: str = Field(..., description="Detailed feedback for the candidate")
    strengths: List[str] = Field(..., description="Identified strengths in the answer")
    improvements: List[str] = Field(..., description="Areas for improvement")
    follow_up_needed: bool = Field(
        ..., description="Whether a follow-up question is recommended"
    )
    response_efficiency: int = Field(default=100, ge=0, le=100, description="Score based on response time and clarification count")


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
    efficiency_score: float = Field(..., description="Average response efficiency")
    total_clarifications: int = Field(..., description="Total clarification requests made")
    average_response_time: float = Field(..., description="Average response time in seconds")
    recommendation: str = Field(..., description="Hiring recommendation")
    summary: str = Field(..., description="Interview summary")
    duration: str = Field(..., description="Total interview duration")


class GeneratedQuestion(BaseModel):
    question: str = Field(..., description="The interview question")
    ideal_answer: str = Field(..., description="Expected ideal answer")
    tags: list[str] = Field(..., description="Question topic tags")
    difficulty: str = Field(..., description="Question difficulty level: simple, intermediate, challenging")
    rubric: Optional[QuestionRubric] = Field(None, description="Structured evaluation rubric")


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
        "- candidate_answer: The candidate's actual response\n"
        "- clarification_count: Number of clarifications requested\n"
        "- response_time_seconds: Time taken to respond\n\n"
        "Your task is to evaluate the candidate_answer against the ideal_answer for the given question.\n"
        "Score each dimension (0-100):\n"
        "- technical_accuracy: How technically correct is the answer?\n"
        "- completeness: How complete/thorough is the answer?\n"
        "- clarity: How clear and well-communicated is the answer?\n"
        "- response_efficiency: Penalize excessive clarifications (>2) and very slow responses (>180s)\n\n"
        "If rubric_scores are provided, evaluate each criterion separately and provide specific feedback.\n"
        "Calculate overall score as the weighted average of all dimensions.\n"
        "Provide constructive feedback, identify strengths, suggest improvements.\n"
        "Set follow_up_needed=true if the answer is unclear or incomplete (score < 60).\n\n"
        "IMPORTANT: Always evaluate the candidate_answer field, never say the answer is missing.\n"
        "Consider response efficiency: Deduct points for excessive clarifications or very slow responses."
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
        self.question_start_time = None  # Track when current question was asked
        self.clarification_count_current = 0  # Track clarifications for current question
        self.is_exam_mode = True  # Exam mode - no immediate feedback
        self.adaptive_questions_used = []  # Track which adaptive questions were used

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

            # Generate initial questions using the AI agent
            try:
                logger.info(f"Generating questions from job description for session {self.id}")
                gen_result = question_generation_agent.run_sync(
                    "Generate a comprehensive set of interview questions for this job description.",
                    deps=job,
                )
                logger.info(f"Question generation agent output: {gen_result}")
                self.question_batch = gen_result.output
                # Convert to TailoredQuestion for compatibility and add rubrics
                self.questions = []
                for q in self.question_batch.questions:
                    rubric = self._create_default_rubric(q.question, q.tags)
                    self.questions.append(TailoredQuestion(
                        question=q.question,
                        ideal_answer=q.ideal_answer,
                        tags=q.tags,
                        difficulty=q.difficulty,
                        rubric=rubric
                    ))
            except Exception as e:
                logger.error(
                    f"AI question generation failed: {str(e)}, using fallback questions"
                )
                # Fallback to default questions if AI selection fails
                fallback_questions = []
                for q in QUESTION_BANK[:5]:
                    rubric = self._create_default_rubric(q["question"], q.get("tags", ["general"]))
                    fallback_questions.append(TailoredQuestion(
                        question=q["question"],
                        ideal_answer=q["ideal_answer"],
                        tags=q.get("tags", ["general"]),
                        difficulty=q.get("difficulty", "intermediate"),
                        rubric=rubric
                    ))
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

    def _create_default_rubric(self, question: str, tags: List[str]) -> QuestionRubric:
        """Create a default rubric based on question content and tags."""
        points = [
            RubricPoint(
                criterion="Technical Accuracy",
                weight=0.4,
                description="Correctness of technical concepts and facts"
            ),
            RubricPoint(
                criterion="Completeness",
                weight=0.3,
                description="Coverage of key aspects and thoroughness"
            ),
            RubricPoint(
                criterion="Clarity & Communication",
                weight=0.3,
                description="Clear explanation and logical structure"
            )
        ]
        return QuestionRubric(points=points)

    def get_current_question(self) -> Optional[str]:
        """Get the current question without advancing the index."""
        if self.current_question_index < len(self.questions):
            # Reset tracking for new question
            if self.question_start_time is None:
                self.question_start_time = datetime.now()
                self.clarification_count_current = 0
            return self.questions[self.current_question_index].question
        return None

    def _select_adaptive_question(self, avg_score: float) -> Optional[TailoredQuestion]:
        """Select an adaptive question based on performance."""
        if avg_score >= 80:
            # High performer - give stretch question
            available_stretch = [q for q in STRETCH_QUESTIONS if q["question"] not in self.adaptive_questions_used]
            if available_stretch:
                selected = available_stretch[0]
                self.adaptive_questions_used.append(selected["question"])
                rubric_data = selected.get("rubric", {})
                rubric = None
                if rubric_data and "points" in rubric_data:
                    rubric = QuestionRubric(
                        points=[RubricPoint(**point) for point in rubric_data["points"]]
                    )
                return TailoredQuestion(
                    question=selected["question"],
                    ideal_answer=selected["ideal_answer"],
                    tags=selected["tags"],
                    difficulty=selected["difficulty"],
                    rubric=rubric or self._create_default_rubric(selected["question"], selected["tags"])
                )
        elif avg_score <= 50:
            # Struggling candidate - give diagnostic question
            available_diagnostic = [q for q in DIAGNOSTIC_QUESTIONS if q["question"] not in self.adaptive_questions_used]
            if available_diagnostic:
                selected = available_diagnostic[0]
                self.adaptive_questions_used.append(selected["question"])
                rubric_data = selected.get("rubric", {})
                rubric = None
                if rubric_data and "points" in rubric_data:
                    rubric = QuestionRubric(
                        points=[RubricPoint(**point) for point in rubric_data["points"]]
                    )
                return TailoredQuestion(
                    question=selected["question"],
                    ideal_answer=selected["ideal_answer"],
                    tags=selected["tags"],
                    difficulty=selected["difficulty"],
                    rubric=rubric or self._create_default_rubric(selected["question"], selected["tags"])
                )
        return None

    def advance_to_next_question(self) -> Optional[str]:
        """Advance to the next question and return it."""
        self.current_question_index += 1
        self.question_start_time = None  # Reset for next question
        
        # Check if we should add an adaptive question
        if len(self.evaluations) >= 2:  # Need at least 2 evaluations to determine performance
            avg_score = sum(e.score for e in self.evaluations) / len(self.evaluations)
            adaptive_q = self._select_adaptive_question(avg_score)
            if adaptive_q:
                # Insert adaptive question at current position
                self.questions.insert(self.current_question_index, adaptive_q)
                logger.info(f"Added adaptive question (avg_score: {avg_score:.1f}): {adaptive_q.question[:50]}...")
        
        return self.get_current_question()

    async def process_answer(self, answer: str) -> tuple[Evaluation, InterviewProgress]:
        """Process the candidate's answer and return evaluation with progress."""
        if self.current_question_index >= len(self.questions):
            raise ValueError("No more questions available")

        current_q = self.questions[self.current_question_index]
        
        # Calculate response time
        response_time = None
        if self.question_start_time:
            response_time = (datetime.now() - self.question_start_time).total_seconds()

        # Create interview turn with enhanced tracking
        turn = InterviewTurn(
            question=current_q.question,
            ideal_answer=current_q.ideal_answer,
            candidate_answer=answer,
            response_time_seconds=response_time,
            clarification_count=self.clarification_count_current
        )

        try:
            # Enhanced evaluation prompt with rubric
            rubric_info = ""
            if current_q.rubric:
                rubric_info = "\n\nEVALUATION RUBRIC:\n"
                for point in current_q.rubric.points:
                    rubric_info += f"- {point.criterion} (weight: {point.weight}): {point.description}\n"

            eval_prompt = (
                f"Please evaluate this interview response:\n\n"
                f"QUESTION: {current_q.question}\n\n"
                f"CANDIDATE'S ANSWER: {answer}\n\n"
                f"EXPECTED ANSWER: {current_q.ideal_answer}\n\n"
                f"RESPONSE TIME: {response_time:.1f}s\n"
                f"CLARIFICATIONS REQUESTED: {self.clarification_count_current}\n"
                f"{rubric_info}\n"
                f"Please provide detailed evaluation with scores for technical accuracy, completeness, clarity, and response efficiency."
            )

            logger.info(f"Evaluating answer for session {self.id}: '{answer[:30]}...' (time: {response_time:.1f}s, clarifications: {self.clarification_count_current})")

            eval_result = await evaluation_agent.run(eval_prompt, deps=turn)
            evaluation = eval_result.output

            # Calculate response efficiency score
            efficiency_score = 100
            if self.clarification_count_current > 2:
                efficiency_score -= (self.clarification_count_current - 2) * 10
            if response_time and response_time > 180:  # 3 minutes
                efficiency_score -= min(30, (response_time - 180) / 60 * 5)
            evaluation.response_efficiency = max(0, efficiency_score)

            # Store the turn and evaluation
            self.turns.append(turn)
            self.evaluations.append(evaluation)

            # Calculate progress
            progress = self._calculate_progress()

            logger.info(
                f"Processed answer for session {self.id}, question {self.current_question_index + 1}, score: {evaluation.score}, efficiency: {evaluation.response_efficiency}"
            )
            return evaluation, progress

        except Exception as e:
            logger.error(f"Failed to process answer for session {self.id}: {str(e)}")
            raise RuntimeError(f"Unable to evaluate answer due to system error: {str(e)}")

    def increment_clarification_count(self):
        """Increment clarification count for current question."""
        self.clarification_count_current += 1

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
        efficiency_score = sum(e.response_efficiency for e in self.evaluations) / len(
            self.evaluations
        )

        # Calculate communication metrics
        total_clarifications = sum(turn.clarification_count for turn in self.turns)
        valid_response_times = [turn.response_time_seconds for turn in self.turns if turn.response_time_seconds is not None]
        average_response_time = sum(valid_response_times) / max(len(valid_response_times), 1)

        # Enhanced recommendation based on multiple factors
        if overall_score >= 80 and efficiency_score >= 70:
            recommendation = "Strong Hire - Candidate demonstrates excellent technical knowledge, communication skills, and efficiency."
        elif overall_score >= 65 and efficiency_score >= 60:
            recommendation = "Hire - Candidate shows good technical competency with reasonable efficiency."
        elif overall_score >= 50:
            if efficiency_score < 50:
                recommendation = "Borderline - Good technical knowledge but needs improvement in communication efficiency."
            else:
                recommendation = "Borderline - Consider for junior roles or with additional training."
        else:
            recommendation = "No Hire - Candidate needs significant development before being ready for this role."

        # Generate enhanced summary
        strengths = []
        improvements = []
        for eval in self.evaluations:
            strengths.extend(eval.strengths)
            improvements.extend(eval.improvements)

        # Add efficiency insights
        efficiency_insights = []
        if total_clarifications == 0:
            efficiency_insights.append("excellent question comprehension")
        elif total_clarifications <= 2:
            efficiency_insights.append("good question comprehension")
        else:
            efficiency_insights.append("frequent clarification requests")

        if average_response_time <= 120:
            efficiency_insights.append("quick response times")
        elif average_response_time <= 300:
            efficiency_insights.append("reasonable response times")
        else:
            efficiency_insights.append("slower response times")

        summary = (
            f"Candidate completed {len(self.evaluations)} questions with an overall score of {overall_score:.1f}%. "
            f"Technical competency: {technical_score:.1f}%, Communication: {communication_score:.1f}%, "
            f"Efficiency: {efficiency_score:.1f}%. "
            f"Key strengths: {', '.join(list(set(strengths))[:3])}. "
            f"Communication efficiency: {', '.join(efficiency_insights)}. "
            f"Areas for improvement: {', '.join(list(set(improvements))[:3])}."
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
            efficiency_score=efficiency_score,
            total_clarifications=total_clarifications,
            average_response_time=average_response_time,
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


# Mock data for /api/session_data
MOCK_SESSION_DATA = {
    "resume_text": "AI Engineer with 3+ years of experience in developing and deploying machine learning models. Proven ability to architect and implement end-to-end MLOps pipelines. Passionate about leveraging AI to solve complex real-world problems.\n- Senior AI Engineer, TechCorp (2021-Present)\n- Led the development of a real-time recommendation engine, improving user engagement by 25%.\n- Designed and deployed scalable training pipelines on AWS using SageMaker, Lambda, and Step Functions.\n- Optimized model inference latency by 40% through quantization and graph optimization.\nSkills: Python, C++, Go, PyTorch, TensorFlow, Scikit-learn, Hugging Face, Docker, Kubernetes, Kubeflow, MLflow, AWS SageMaker, SQL, NoSQL, Spark, Pandas, NumPy.",
    "job_description": "Role: AI Engineer\nResponsibilities:\n- Design, build, train, and deploy machine learning models.\n- Develop and maintain scalable MLOps infrastructure for model lifecycle management.\n- Collaborate with data scientists to productize ML prototypes.\n- Research and implement state-of-the-art algorithms to tackle business challenges.\n- Ensure model performance, scalability, and reliability in production.\nQualifications:\n- BS/MS in Computer Science or related field.\n- Strong experience in Python and ML frameworks (PyTorch, TensorFlow).\n- Hands-on experience with cloud platforms (AWS, GCP, or Azure).\n- Solid software engineering fundamentals.\n- Familiarity with CI/CD, Docker, and Kubernetes is a plus.",
    "questions": [
        "What is the difference between PyTorch and TensorFlow?",
        "How would you deploy a machine learning model using AWS SageMaker?"
    ],
    "answers": [
        "PyTorch is more pythonic and dynamic, while TensorFlow is more static and production-oriented."
    ]
}

@app.get("/api/session_data")
async def get_mock_session_data():
    """Return mock session data for frontend initialization."""
    return MOCK_SESSION_DATA

@app.post("/session")
async def create_session(req: ResumeInput):
    """Create a new interview session."""
    try:
        # Use provided or mock data
        resume = req.resume_text or MOCK_SESSION_DATA["resume_text"]
        job = req.job_description or MOCK_SESSION_DATA["job_description"]
        questions = req.questions or MOCK_SESSION_DATA.get("questions")
        answers = req.answers or MOCK_SESSION_DATA.get("answers")

        sess = EnhancedInterviewSession(resume, job)
        sessions[sess.id] = sess

        # If questions are provided, override the generated questions
        if questions:
            sess.questions = [
                TailoredQuestion(
                    question=q,
                    ideal_answer="",  # Could be filled by AI or left blank
                    tags=[],
                    difficulty="intermediate"
                ) for q in questions
            ]
        # If answers are provided, pre-fill interview turns (optional, for demo)
        if answers:
            for idx, ans in enumerate(answers):
                if idx < len(sess.questions):
                    turn = InterviewTurn(
                        question=sess.questions[idx].question,
                        ideal_answer=sess.questions[idx].ideal_answer,
                        candidate_answer=ans
                    )
                    sess.turns.append(turn)

        first_question = sess.get_current_question()
        if not first_question:
            raise HTTPException(500, "No questions available for this candidate")

        return {
            "session_id": sess.id,
            "first_question": first_question,
            "context_summary": sess.context.summary,
            "total_questions": len(sess.questions),
            "selection_reasoning": getattr(sess.question_batch, 'reasoning', ''),
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
        # Increment clarification count
        session.increment_clarification_count()
        
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
            
            # Check if too many clarifications
            if session.clarification_count_current > 2:
                clarification += f"\n\nNote: You have requested {session.clarification_count_current} clarifications for this question. Please try to provide your best answer."
            
            # Always return the clarification to the user
            await websocket.send_json({"type": "clarification", "data": {"clarification": clarification}})
        except Exception as e:
            logger.error(f"Clarification agent failed: {e}")
            clarification = "I'm sorry, I couldn't generate a clarification at this time. Please try to answer the question as best you can."
            await websocket.send_json({"type": "clarification", "data": {"clarification": clarification}})

    async def send_unrelated(user_question: str):
        await websocket.send_json({"type": "unrelated", "data": {"unrelated": "Please answer the question as best you can."}})

    
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
            elif message_type == MessageType.unrelated:
                await send_unrelated(answer_strip)
                continue
            if answer_strip.lower() in ["quit", "exit", "end"]:
                final_report = session.generate_final_report()
                await websocket.send_json(
                    {"type": "final_report", "data": final_report.model_dump(mode="json")}
                )
                await websocket.close()
                break

            # Process the answer
            evaluation, progress = await session.process_answer(answer)

            # EXAM MODE: No immediate feedback, just acknowledgment and progress
            if session.is_exam_mode:
                # Send simple acknowledgment
                await websocket.send_json({
                    "type": "answer_received",
                    "data": {
                        "message": "Answer received. Moving to next question...",
                        "question_number": progress.current_question,
                        "total_questions": progress.total_questions
                    }
                })
                
                # Send progress update (but without scores)
                await websocket.send_json({
                    "type": "progress", 
                    "data": {
                        "current_question": progress.current_question,
                        "total_questions": progress.total_questions,
                        "time_elapsed": progress.time_elapsed
                        # Note: No average_score in exam mode
                    }
                })
            else:
                # COACHING MODE: Immediate feedback (not implemented in this version)
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
                            "response_efficiency": evaluation.response_efficiency,
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
                # Interview complete - show final report
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
            display: none;
        }
        .modal-content {
            display: none;
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
            display: none;
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
            <div id="contextPanel" class="context-panel" style="margin-bottom: 24px; padding: 18px 24px; background: #eaf6ff; border-radius: 10px; border: 1.5px solid #b6c6e3; color: #234;">
                <!-- Context info will be injected here -->
            </div>
            <div id="interviewSection">
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

        async function startInterviewWithMockData() {
            showLoading('Loading session data...');
            try {
                const resp = await fetch('/api/session_data');
                const mockData = await resp.json();
                // Start session with mock data
                const response = await fetch('/session', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(mockData)
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
                }
                const data = await response.json();
                currentSession = data;
                // Show context info in the info panel, not in chat
                const contextPanel = document.getElementById('contextPanel');
                contextPanel.innerHTML = `
                    <strong>Interview Context</strong><br>
                    <span style="color:#357;">${data.context_summary}</span><br>
                    <span style="font-size:0.98em;">Questions selected: <b>${data.total_questions}</b></span><br>
                    <span style="font-size:0.98em;">Reasoning: <i>${data.selection_reasoning}</i></span>
                `;
                // Show the first question as a bot message in the chat
                addMessage('bot', `📝 <strong>First Question:</strong> ${data.first_question}`);
                connectWebSocket(data.session_id);
            } catch (error) {
                console.error('Error creating session:', error);
                alert('Failed to create interview session. Check the console for details.');
            } finally {
                hideLoading();
            }
        }

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
                case 'answer_received':
                    showAnswerReceived(message.data);
                    break;
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

        function showAnswerReceived(data) {
            const receivedHtml = `
                <div class="message system">
                    ✅ ${data.message}<br>
                    <small>Question ${data.question_number} of ${data.total_questions} completed</small>
                </div>
            `;
            document.getElementById('chat').innerHTML += receivedHtml;
            scrollToBottom();
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
                            <th>Efficiency</th>
                        </tr>
                        <tr>
                            <td class="score-cell score-${scoreClass}">${data.score}/100</td>
                            <td>${data.technical_accuracy}/100</td>
                            <td>${data.completeness}/100</td>
                            <td>${data.clarity}/100</td>
                            <td>${data.response_efficiency || 'N/A'}/100</td>
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
            // In exam mode, don't show average score
            const progressContent = data.average_score !== undefined 
                ? `Current Average: ${data.average_score.toFixed(1)}/100<br>`
                : '';
            
            const progressHtml = `
                <div class="message progress">
                    <strong>📈 Progress Update</strong><br>
                    Question ${data.current_question}/${data.total_questions} completed<br>
                    ${progressContent}
                    Time Elapsed: ${data.time_elapsed}
                </div>
            `;
            document.getElementById('chat').innerHTML += progressHtml;
            scrollToBottom();
        }

        function showFinalReport(data) {
            const scoreClass = data.overall_score >= 70 ? 'high' : data.overall_score >= 50 ? 'medium' : 'low';
            const efficiencyClass = data.efficiency_score >= 70 ? 'high' : data.efficiency_score >= 50 ? 'medium' : 'low';
            
            // Build enhanced Q&A table with response times and clarifications
            let qaTable = `<table class="evaluation-table" style="margin-top:18px;">
                <tr>
                    <th>#</th>
                    <th>Question</th>
                    <th>Your Answer</th>
                    <th>Ideal Answer</th>
                    <th>Score</th>
                    <th>Time</th>
                    <th>Clarifications</th>
                </tr>`;
            for (let i = 0; i < data.turns.length; i++) {
                const turn = data.turns[i];
                const eval_ = data.evaluations[i];
                const turnScoreClass = eval_ && eval_.score >= 70 ? 'score-high' : eval_ && eval_.score >= 50 ? 'score-medium' : 'score-low';
                const responseTime = turn.response_time_seconds ? `${Math.round(turn.response_time_seconds)}s` : 'N/A';
                qaTable += `<tr>
                    <td>${i + 1}</td>
                    <td style="min-width:160px;max-width:260px;">${turn.question}</td>
                    <td style="min-width:140px;max-width:220px;">${turn.candidate_answer}</td>
                    <td style="min-width:140px;max-width:220px;">${turn.ideal_answer}</td>
                    <td class="score-cell ${turnScoreClass}">${eval_ ? eval_.score : '-'}/100</td>
                    <td>${responseTime}</td>
                    <td>${turn.clarification_count || 0}</td>
                </tr>`;
            }
            qaTable += `</table>`;

            const reportHtml = `
                <div class="message bot">
                    <div class="content-wrapper">
                        <strong>🎯 Interview Complete!</strong><br><br>
                        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px;">
                            <div><span class="score ${scoreClass}">Overall: ${data.overall_score.toFixed(1)}/100</span></div>
                            <div><span class="score">Technical: ${data.technical_score.toFixed(1)}/100</span></div>
                            <div><span class="score">Communication: ${data.communication_score.toFixed(1)}/100</span></div>
                            <div><span class="score ${efficiencyClass}">Efficiency: ${data.efficiency_score.toFixed(1)}/100</span></div>
                        </div>
                        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 15px; font-size: 0.9em;">
                            <div>📋 Total Clarifications: <strong>${data.total_clarifications}</strong></div>
                            <div>⏱️ Avg Response Time: <strong>${Math.round(data.average_response_time)}s</strong></div>
                            <div>🕒 Duration: <strong>${data.duration}</strong></div>
                        </div>
                        <strong>📋 Summary:</strong> ${data.summary}<br><br>
                        <strong>🎯 Recommendation:</strong> ${data.recommendation}<br><br>
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

        // Start interview automatically on page load
        window.onload = startInterviewWithMockData;
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_INTERFACE




if __name__ == "__main__":
    import sys

    logger.info("Starting Enhanced Agentic Interview Bot...")
    uvicorn.run(app, host="0.0.0.0", port=8635, log_level="info")
