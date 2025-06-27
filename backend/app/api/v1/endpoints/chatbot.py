from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from typing import Optional
import logging

from core.security import decode_access_token, TokenData
from services.mcp_sqlalchemy_server.client import Chat
from core.database import get_session

router = APIRouter()

logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_session)):
    await websocket.accept()
    try:
        # First message is the token
        token = await websocket.receive_text()
        token_data: Optional[TokenData] = decode_access_token(token)

        if not token_data or not token_data.employer_id:
            await websocket.send_text("Authentication failed. Closing connection.")
            await websocket.close(code=1008)
            return

        employer_id = token_data.employer_id
        from crud.crud_company import get_company

        company = get_company(db=next(get_session()), employer_id=employer_id)
        logger.info(f"company: {company}")
        # Initialize chat client with employer_id
        chat = Chat(company=company.model_dump())

        # Start the MCP server process
        async with chat.agent.run_mcp_servers():
            # Send a welcome message
            initial_response = await chat.run_interaction("Hello")
            await websocket.send_text(initial_response)

            while True:
                # Receive message from frontend
                prompt = await websocket.receive_text()

                # Get response from agent
                response = await chat.run_interaction(prompt)

                # Send response back to frontend
                await websocket.send_text(response)

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        await websocket.close(code=1011)


async def send_initial_message(websocket: WebSocket, company_id: int):
    try:
        await websocket.send_json(
            {
                "sender": "bot",
                "message": "Welcome to the chatbot! How can I assist you today?",
                "company_id": company_id,
            }
        )
    except Exception as e:
        logger.error(f"Error sending initial message: {e}", exc_info=True)


@router.websocket("/ws/{company_id}")
async def websocket_endpoint(websocket: WebSocket, company_id: int):
    await websocket.accept()
    logger.info(f"New client connected for company: {company_id}")

    await send_initial_message(websocket, company_id)

    try:
        while True:
            data = await websocket.receive_text()
            # Here you would process the data and generate a response
            # For now, we'll just echo it back.
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from company: {company_id}")
    except Exception as e:
        logger.error(
            f"An error occurred in websocket for company {company_id}: {e}",
            exc_info=True,
        )
