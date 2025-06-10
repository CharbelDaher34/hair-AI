from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session
from typing import Optional

from core.security import decode_access_token, TokenData
from services.mcp_sqlalchemy_server.client import Chat
from core.database import get_session
router = APIRouter()

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
        print(f"company: {company}")
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
        print("Client disconnected")
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.close(code=1011)
