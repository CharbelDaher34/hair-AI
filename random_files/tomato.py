#!/usr/bin/env python3
import os

os.environ["GEMINI_API_KEY"] = "AIzaSyDp8n_AmYsspADJBaNpkJvBdlch1-9vkhw"
"""
Multiagent System using PydanticAI

This system demonstrates a comprehensive multiagent architecture with:
- Research Agent: Conducts research and gathers information
- Analysis Agent: Analyzes and processes data
- Writing Agent: Creates structured outputs
- Coordinator Agent: Orchestrates the entire workflow
- Quality Assurance Agent: Reviews and validates outputs

The system uses shared dependencies and demonstrates agent delegation.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Union, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage


# =============================================================================
# Data Models and Types
# =============================================================================


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchTopic(BaseModel):
    topic: str = Field(description="The main research topic")
    subtopics: List[str] = Field(description="List of subtopics to explore")
    keywords: List[str] = Field(description="Keywords for research")
    priority: TaskPriority = Field(description="Priority level of the research")


class ResearchFindings(BaseModel):
    topic: str
    key_points: List[str] = Field(description="Key findings from research")
    sources: List[str] = Field(description="Sources of information")
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Confidence in findings"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class AnalysisResult(BaseModel):
    summary: str = Field(description="Summary of analysis")
    insights: List[str] = Field(description="Key insights discovered")
    recommendations: List[str] = Field(description="Actionable recommendations")
    risk_factors: List[str] = Field(description="Potential risks identified")
    confidence_level: float = Field(ge=0.0, le=1.0)


class WrittenReport(BaseModel):
    title: str
    executive_summary: str
    main_content: str
    conclusions: List[str]
    next_steps: List[str]
    word_count: int


class QualityAssessment(BaseModel):
    quality_score: float = Field(ge=0.0, le=10.0, description="Overall quality score")
    strengths: List[str] = Field(description="Identified strengths")
    weaknesses: List[str] = Field(description="Areas for improvement")
    suggestions: List[str] = Field(description="Specific improvement suggestions")
    approved: bool = Field(description="Whether the work is approved")


class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    research_findings: Optional[ResearchFindings] = None
    analysis_result: Optional[AnalysisResult] = None
    written_report: Optional[WrittenReport] = None
    quality_assessment: Optional[QualityAssessment] = None
    completion_time: datetime = Field(default_factory=datetime.now)


@dataclass
class SharedDependencies:
    """Shared dependencies across all agents"""

    task_id: str
    data_store: Dict[str, Any] = field(default_factory=dict)
    message_history: Dict[str, List[ModelMessage]] = field(default_factory=dict)
    current_date: date = field(default_factory=date.today)

    def store_data(self, key: str, value: Any) -> None:
        """Store data that can be accessed by other agents"""
        self.data_store[key] = value

    def get_data(self, key: str) -> Any:
        """Retrieve stored data"""
        return self.data_store.get(key)


# =============================================================================
# Agent Definitions
# =============================================================================

# Research Agent - Gathers and organizes information
research_agent = Agent(
    "google-gla:gemini-2.0-flash",
    deps_type=SharedDependencies,
    result_type=ResearchFindings,
    system_prompt=(
        "You are a research specialist. Your role is to conduct thorough research "
        "on given topics, identify key information, and organize findings in a "
        "structured manner. Focus on accuracy, relevance, and comprehensive coverage."
    ),
)


@research_agent.system_prompt
async def add_research_context(ctx: RunContext[SharedDependencies]) -> str:
    return f"Current date: {ctx.deps.current_date}. Task ID: {ctx.deps.task_id}"


@research_agent.tool
async def store_research_data(
    ctx: RunContext[SharedDependencies], key: str, data: str
) -> str:
    """Store research data for use by other agents"""
    ctx.deps.store_data(f"research_{key}", data)
    return f"Stored research data under key: research_{key}"


@research_agent.tool
async def get_stored_data(ctx: RunContext[SharedDependencies], key: str) -> str:
    """Retrieve previously stored data"""
    data = ctx.deps.get_data(key)
    return str(data) if data else "No data found for this key"


# Analysis Agent - Processes and analyzes information
analysis_agent = Agent(
    "google-gla:gemini-2.0-flash",
    deps_type=SharedDependencies,
    result_type=AnalysisResult,
    system_prompt=(
        "You are an analytical specialist. Your role is to analyze research findings, "
        "identify patterns, draw insights, and provide actionable recommendations. "
        "Focus on critical thinking, logical reasoning, and practical applications."
    ),
)


@analysis_agent.system_prompt
async def add_analysis_context(ctx: RunContext[SharedDependencies]) -> str:
    return f"Task ID: {ctx.deps.task_id}. Access stored research data as needed."


@analysis_agent.tool
async def analyze_research_findings(
    ctx: RunContext[SharedDependencies], research_key: str
) -> str:
    """Analyze previously stored research findings"""
    research_data = ctx.deps.get_data(research_key)
    if not research_data:
        return "No research data found to analyze"

    # Store analysis progress
    ctx.deps.store_data("analysis_in_progress", True)
    return f"Analyzing research data: {research_data}"


@analysis_agent.tool
async def store_analysis_insight(
    ctx: RunContext[SharedDependencies], insight: str, confidence: float
) -> str:
    """Store an analytical insight with confidence score"""
    insights = ctx.deps.get_data("analysis_insights") or []
    insights.append({"insight": insight, "confidence": confidence})
    ctx.deps.store_data("analysis_insights", insights)
    return f"Stored insight with confidence {confidence}"


# Writing Agent - Creates structured written outputs
writing_agent = Agent(
    "google-gla:gemini-2.0-flash",
    deps_type=SharedDependencies,
    result_type=WrittenReport,
    system_prompt=(
        "You are a professional writer and editor. Your role is to create clear, "
        "well-structured, and engaging written content based on research and analysis. "
        "Focus on clarity, coherence, and professional presentation."
    ),
)


@writing_agent.system_prompt
async def add_writing_context(ctx: RunContext[SharedDependencies]) -> str:
    return f"Task ID: {ctx.deps.task_id}. Create professional documentation."


@writing_agent.tool
async def get_research_for_writing(ctx: RunContext[SharedDependencies]) -> str:
    """Retrieve research findings for writing"""
    research_data = ctx.deps.get_data("research_findings")
    analysis_data = ctx.deps.get_data("analysis_result")

    combined_data = {"research": research_data, "analysis": analysis_data}
    return json.dumps(combined_data, indent=2)


@writing_agent.tool
async def calculate_word_count(ctx: RunContext[SharedDependencies], text: str) -> int:
    """Calculate word count for text"""
    word_count = len(text.split())
    ctx.deps.store_data("document_word_count", word_count)
    return word_count


# Quality Assurance Agent - Reviews and validates outputs
qa_agent = Agent(
    "google-gla:gemini-2.0-flash",
    deps_type=SharedDependencies,
    result_type=QualityAssessment,
    system_prompt=(
        "You are a quality assurance specialist. Your role is to review work products, "
        "assess their quality, identify strengths and weaknesses, and provide constructive "
        "feedback for improvement. Be thorough, fair, and constructive."
    ),
)


@qa_agent.system_prompt
async def add_qa_context(ctx: RunContext[SharedDependencies]) -> str:
    return f"Task ID: {ctx.deps.task_id}. Review all work products for quality."


@qa_agent.tool
async def review_document(
    ctx: RunContext[SharedDependencies], document_type: str
) -> str:
    """Review a specific type of document"""
    document_data = ctx.deps.get_data(f"{document_type}_document")
    if not document_data:
        return f"No {document_type} document found to review"

    ctx.deps.store_data("qa_review_in_progress", document_type)
    return f"Reviewing {document_type} document: {str(document_data)[:200]}..."


@qa_agent.tool
async def store_quality_feedback(
    ctx: RunContext[SharedDependencies], feedback_type: str, feedback: str
) -> str:
    """Store quality feedback"""
    feedback_data = ctx.deps.get_data("qa_feedback") or {}
    feedback_data[feedback_type] = feedback
    ctx.deps.store_data("qa_feedback", feedback_data)
    return f"Stored {feedback_type} feedback"


# Coordinator Agent - Orchestrates the entire workflow
coordinator_agent = Agent(
    "google-gla:gemini-2.0-flash",
    deps_type=SharedDependencies,
    result_type=TaskResult,
    system_prompt=(
        "You are a project coordinator. Your role is to orchestrate the work of "
        "multiple specialist agents, ensure proper workflow, and compile final results. "
        "Coordinate effectively and ensure all agents contribute to the final outcome."
    ),
)


@coordinator_agent.system_prompt
async def add_coordinator_context(ctx: RunContext[SharedDependencies]) -> str:
    return f"Coordinating task {ctx.deps.task_id} on {ctx.deps.current_date}"


@coordinator_agent.tool
async def delegate_research(
    ctx: RunContext[SharedDependencies], research_topic: str, subtopics: List[str]
) -> ResearchFindings:
    """Delegate research task to the research agent"""
    topic = ResearchTopic(
        topic=research_topic,
        subtopics=subtopics,
        keywords=subtopics,  # Simple mapping for demo
        priority=TaskPriority.HIGH,
    )

    result = await research_agent.run(
        f"Research the following topic comprehensively: {topic.topic}. "
        f"Focus on these subtopics: {', '.join(topic.subtopics)}",
        deps=ctx.deps,
        usage=ctx.usage,
    )

    # Store research findings for other agents
    ctx.deps.store_data("research_findings", result.output)
    return result.output


@coordinator_agent.tool
async def delegate_analysis(ctx: RunContext[SharedDependencies]) -> AnalysisResult:
    """Delegate analysis task to the analysis agent"""
    research_findings = ctx.deps.get_data("research_findings")
    if not research_findings:
        raise ValueError("No research findings available for analysis")

    result = await analysis_agent.run(
        f"Analyze the research findings and provide insights and recommendations. "
        f"Research data: {research_findings}",
        deps=ctx.deps,
        usage=ctx.usage,
    )

    # Store analysis results
    ctx.deps.store_data("analysis_result", result.output)
    return result.output


@coordinator_agent.tool
async def delegate_writing(
    ctx: RunContext[SharedDependencies], document_title: str
) -> WrittenReport:
    """Delegate writing task to the writing agent"""
    result = await writing_agent.run(
        f"Create a comprehensive report titled '{document_title}' based on "
        f"the available research and analysis data.",
        deps=ctx.deps,
        usage=ctx.usage,
    )

    # Store written report
    ctx.deps.store_data("written_report", result.output)
    return result.output


@coordinator_agent.tool
async def delegate_quality_assurance(
    ctx: RunContext[SharedDependencies],
) -> QualityAssessment:
    """Delegate quality assurance task to the QA agent"""
    written_report = ctx.deps.get_data("written_report")
    if not written_report:
        raise ValueError("No written report available for QA review")

    result = await qa_agent.run(
        f"Review the written report for quality, accuracy, and completeness. "
        f"Provide constructive feedback and recommendations.",
        deps=ctx.deps,
        usage=ctx.usage,
    )

    # Store QA assessment
    ctx.deps.store_data("quality_assessment", result.output)
    return result.output


# =============================================================================
# Workflow Functions
# =============================================================================


async def run_multiagent_workflow(
    task_description: str,
    research_topic: str,
    subtopics: List[str],
    document_title: str,
) -> TaskResult:
    """
    Execute the complete multiagent workflow
    """
    # Initialize shared dependencies
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    deps = SharedDependencies(task_id=task_id)

    print(f"🚀 Starting multiagent workflow for task: {task_id}")
    print(f"📋 Task description: {task_description}")
    print(f"🔍 Research topic: {research_topic}")
    print(f"📄 Document title: {document_title}")
    print("-" * 60)

    try:
        # Step 1: Coordinate the entire workflow
        result = await coordinator_agent.run(
            f"Coordinate a comprehensive workflow for: {task_description}. "
            f"Research topic: {research_topic}. "
            f"Document title: {document_title}. "
            f"Subtopics: {', '.join(subtopics)}. "
            f"Execute research, analysis, writing, and quality assurance in sequence.",
            deps=deps,
        )

        print("✅ Multiagent workflow completed successfully!")
        print(f"📊 Total usage: {result.usage()}")

        return result.output

    except Exception as e:
        print(f"❌ Workflow failed: {str(e)}")
        return TaskResult(task_id=task_id, status=TaskStatus.FAILED)


async def demonstrate_agent_capabilities():
    """
    Demonstrate various capabilities of the multiagent system
    """
    print("🎯 PydanticAI Multiagent System Demonstration")
    print("=" * 60)

    # Example 1: Technology Research and Analysis
    print("\n📊 Example 1: Technology Research and Analysis")
    result1 = await run_multiagent_workflow(
        task_description="Analyze the current state and future prospects of artificial intelligence in healthcare",
        research_topic="AI in Healthcare",
        subtopics=[
            "Medical Diagnosis",
            "Drug Discovery",
            "Patient Care",
            "Regulatory Challenges",
        ],
        document_title="AI in Healthcare: Current State and Future Prospects",
    )

    print(f"\n📋 Task Result 1:")
    print(f"  - Task ID: {result1.task_id}")
    print(f"  - Status: {result1.status}")
    print(f"  - Completion Time: {result1.completion_time}")

    if result1.research_findings:
        print(
            f"  - Research Confidence: {result1.research_findings.confidence_score:.2f}"
        )
    if result1.analysis_result:
        print(
            f"  - Analysis Confidence: {result1.analysis_result.confidence_level:.2f}"
        )
    if result1.written_report:
        print(f"  - Report Word Count: {result1.written_report.word_count}")
    if result1.quality_assessment:
        print(f"  - Quality Score: {result1.quality_assessment.quality_score:.1f}/10")
        print(f"  - Approved: {result1.quality_assessment.approved}")

    # Example 2: Business Strategy Analysis
    print("\n💼 Example 2: Business Strategy Analysis")
    result2 = await run_multiagent_workflow(
        task_description="Develop a strategic analysis for sustainable business practices in the technology sector",
        research_topic="Sustainable Tech Business Practices",
        subtopics=[
            "Green Computing",
            "Circular Economy",
            "ESG Compliance",
            "Cost-Benefit Analysis",
        ],
        document_title="Strategic Guide to Sustainable Technology Business Practices",
    )

    print(f"\n📋 Task Result 2:")
    print(f"  - Task ID: {result2.task_id}")
    print(f"  - Status: {result2.status}")
    print(f"  - Completion Time: {result2.completion_time}")

    if result2.quality_assessment:
        print(f"  - Quality Score: {result2.quality_assessment.quality_score:.1f}/10")
        print(f"  - Approved: {result2.quality_assessment.approved}")

    print("\n🎉 Demonstration completed!")
    print("📈 System Features Demonstrated:")
    print("  ✓ Agent delegation and coordination")
    print("  ✓ Shared dependencies and data flow")
    print("  ✓ Structured output types with Pydantic")
    print("  ✓ Tool usage and context management")
    print("  ✓ Multi-step workflow orchestration")
    print("  ✓ Quality assurance and validation")


# =============================================================================
# Main Execution
# =============================================================================


async def main():
    """
    Main function to run the multiagent system demonstration
    """
    try:
        await demonstrate_agent_capabilities()
    except Exception as e:
        print(f"❌ System error: {str(e)}")
        print(
            "💡 Make sure you have set up your OpenAI API key in environment variables"
        )


if __name__ == "__main__":
    # Run the multiagent system
    asyncio.run(main())
