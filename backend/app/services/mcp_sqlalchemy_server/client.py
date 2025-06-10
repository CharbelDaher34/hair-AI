import os
import asyncio
from typing import List

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.messages import ModelMessage


class Chat:
    """A chat client that interacts with a Pydantic-AI agent and maintains conversation history."""

    def __init__(self, model: str = "gemini-2.0-flash", company: dict = None):
        """
        Initializes the chat client.

        Args:
            model: The name of the LLM model to use.
            company: The company to filter database queries by.
        """
        employer_id = company["id"]
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
            system_prompt=f'''You are a helpful assistant that can query the database for the company with id {employer_id}.
Use tools to get information about the database to answer the user's question.
Always get the tables info first before writing the query to get the needed information.

You are working for the company {company["name"]} with id {employer_id} only, you can only access the data of this company.
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