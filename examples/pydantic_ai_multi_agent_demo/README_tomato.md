# PydanticAI Multiagent System

This is a comprehensive multiagent system built using the newly released **pydantic_ai** library. The system demonstrates advanced agent coordination, delegation, and workflow orchestration.

## System Architecture

The multiagent system consists of 5 specialized agents:

### 🔍 Research Agent
- **Role**: Conducts thorough research and gathers information
- **Capabilities**: Topic research, data collection, source identification
- **Output**: Structured research findings with confidence scores

### 📊 Analysis Agent  
- **Role**: Analyzes and processes research data
- **Capabilities**: Pattern identification, insight generation, risk assessment
- **Output**: Comprehensive analysis with recommendations

### ✍️ Writing Agent
- **Role**: Creates structured written outputs
- **Capabilities**: Professional report writing, content structuring
- **Output**: Well-formatted reports with executive summaries

### 🔍 Quality Assurance Agent
- **Role**: Reviews and validates all outputs
- **Capabilities**: Quality assessment, feedback generation, approval decisions
- **Output**: Quality scores and improvement suggestions

### 🎯 Coordinator Agent
- **Role**: Orchestrates the entire workflow
- **Capabilities**: Agent delegation, workflow management, result compilation
- **Output**: Complete task results with all agent outputs

## Key Features

- **Agent Delegation**: Agents can delegate tasks to other specialized agents
- **Shared Dependencies**: All agents share context and data through `SharedDependencies`
- **Structured Outputs**: All outputs are validated using Pydantic models
- **Tool Integration**: Agents have access to custom tools for enhanced capabilities
- **Workflow Orchestration**: Complex multi-step workflows with proper sequencing
- **Quality Assurance**: Built-in QA process for all outputs

## Installation

1. Install dependencies:
```bash
pip install -r requirements_tomato.txt
```

2. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

Run the multiagent system:

```bash
python tomato.py
```

The system will demonstrate two example workflows:
1. **Technology Research**: AI in Healthcare analysis
2. **Business Strategy**: Sustainable tech business practices

## Example Output

```
🎯 PydanticAI Multiagent System Demonstration
============================================================

📊 Example 1: Technology Research and Analysis
🚀 Starting multiagent workflow for task: task_20250103_143022
📋 Task description: Analyze the current state and future prospects of artificial intelligence in healthcare
🔍 Research topic: AI in Healthcare
📄 Document title: AI in Healthcare: Current State and Future Prospects
------------------------------------------------------------
✅ Multiagent workflow completed successfully!
📊 Total usage: Usage(requests=15, request_tokens=2341, response_tokens=892, total_tokens=3233)

📋 Task Result 1:
  - Task ID: task_20250103_143022
  - Status: completed
  - Research Confidence: 0.85
  - Analysis Confidence: 0.78
  - Report Word Count: 1247
  - Quality Score: 8.5/10
  - Approved: True
```

## Code Structure

### Data Models
- `ResearchFindings`: Structured research outputs
- `AnalysisResult`: Analysis insights and recommendations  
- `WrittenReport`: Professional report format
- `QualityAssessment`: Quality scores and feedback
- `TaskResult`: Complete workflow results

### Shared Dependencies
- `SharedDependencies`: Context and data sharing between agents
- Data store for inter-agent communication
- Message history tracking
- Task coordination

### Agent Tools
Each agent has specialized tools:
- **Research**: Data storage and retrieval
- **Analysis**: Research data analysis, insight storage
- **Writing**: Content retrieval, word counting
- **QA**: Document review, feedback storage
- **Coordinator**: Agent delegation tools

## Customization

You can easily customize the system by:

1. **Adding new agents**: Create new `Agent` instances with specific roles
2. **Modifying workflows**: Update the coordinator's delegation logic
3. **Adding tools**: Register new tools for enhanced capabilities
4. **Changing models**: Switch between different LLM providers
5. **Custom data models**: Define new Pydantic models for your use case

## Advanced Features

- **Async/Await**: Full asynchronous operation for performance
- **Type Safety**: Complete type checking with Pydantic
- **Error Handling**: Robust error handling and recovery
- **Usage Tracking**: Token usage monitoring across all agents
- **Message History**: Conversation continuity between agents
- **Functional Programming**: Clean, functional code structure

## Requirements

- Python 3.8+
- pydantic-ai
- pydantic
- OpenAI API key

## License

This is a demonstration project showcasing pydantic_ai capabilities.
