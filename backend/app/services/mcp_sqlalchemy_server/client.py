import os
import asyncio
from typing import List

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.messages import ModelMessage


class Chat:
    """A chat client that interacts with a Pydantic-AI agent and maintains conversation history."""

    def __init__(self, model: str = "gemini-2.0-flash", employer_id: int = 1):
        """
        Initializes the chat client.

        Args:
            model: The name of the LLM model to use.
            employer_id: The employer ID to filter database queries by.
        """
        # Create MCP server with employer_id as argument
        server = MCPServerStdio(
            command="uv",
            args=["run", "server.py", str(employer_id)],
            cwd=os.path.dirname(__file__)
        )

        if "GEMINI_API_KEY" not in os.environ:
            # This was hardcoded in the original file.
            # For production, prefer loading from a secure source.
            os.environ["GEMINI_API_KEY"] = "AIzaSyDp8n_AmYsspADJBaNpkJvBdlch1-9vkhw"

        self.agent = Agent(
            model,
            mcp_servers=[server],
            system_prompt=f'''You are a helpful assistant that can help with SQL queries for employer ID {employer_id}. All database queries will be automatically filtered to show only data related to this employer. You can use the tools provided to you to help with your task. 
The people using are not technical, so you need to be very clear and concise in your responses.
You can use the tools provided to you to help with your task.
You can also use the tools to get more information about the data you are querying.
'''
        )
        
        self.message_history: List[ModelMessage] = []
        self.employer_id = employer_id

    async def run_interaction(self, prompt: str) -> str:
        """
        Sends a prompt to the agent and returns the response, maintaining conversation history.

        Args:
            prompt: The user's input prompt.
        
        Returns:
            The agent's response.
        """
        result = await self.agent.run(prompt, message_history=self.message_history)
        self.message_history = result.all_messages()
        return result.output