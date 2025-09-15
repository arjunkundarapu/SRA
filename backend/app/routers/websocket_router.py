from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
from datetime import datetime
from ..services import interview_service
from ..schemas import WebSocketMessage

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_to_session(self, message: str, session_id: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection might be closed, remove it
                    self.active_connections[session_id].remove(connection)

manager = ConnectionManager()

@router.websocket("/ws/interview/{session_id}")
async def websocket_interview_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time interview conversation
    """
    await manager.connect(websocket, session_id)
    
    try:
        # Send welcome message
        welcome_message = WebSocketMessage(
            type="system",
            session_id=session_id,
            content="Connected to interview session. You can start chatting!",
            timestamp=datetime.now().isoformat()
        )
        await manager.send_personal_message(welcome_message.json(), websocket)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse the incoming message
                message_data = json.loads(data)
                
                if message_data.get("type") == "user_message":
                    user_message = message_data.get("content", "")
                    
                    # Send user message to all connections in this session
                    user_ws_message = WebSocketMessage(
                        type="user_message",
                        session_id=session_id,
                        content=user_message,
                        timestamp=datetime.now().isoformat(),
                        user_id=message_data.get("user_id", "applicant")
                    )
                    await manager.send_to_session(user_ws_message.json(), session_id)
                    
                    # Process the message through the interview service
                    try:
                        response = await interview_service.process_answer_and_get_next(
                            session_id, user_message
                        )
                        
                        # Send AI response back to all connections
                        ai_ws_message = WebSocketMessage(
                            type="ai_response",
                            session_id=session_id,
                            content=response["message"],
                            timestamp=datetime.now().isoformat(),
                            user_id="interviewer"
                        )
                        await manager.send_to_session(ai_ws_message.json(), session_id)
                        
                    except Exception as e:
                        # Send error message
                        error_message = WebSocketMessage(
                            type="error",
                            session_id=session_id,
                            content=f"Interview processing error: {str(e)}",
                            timestamp=datetime.now().isoformat()
                        )
                        await manager.send_personal_message(error_message.json(), websocket)
                
                elif message_data.get("type") == "ping":
                    # Handle ping/pong for connection health
                    pong_message = WebSocketMessage(
                        type="pong",
                        session_id=session_id,
                        content="pong",
                        timestamp=datetime.now().isoformat()
                    )
                    await manager.send_personal_message(pong_message.json(), websocket)
                
                elif message_data.get("type") == "end_interview":
                    # Handle interview completion
                    try:
                        report = await interview_service.generate_report(session_id)
                        
                        completion_message = WebSocketMessage(
                            type="interview_completed",
                            session_id=session_id,
                            content="Interview completed successfully! Report has been generated.",
                            timestamp=datetime.now().isoformat()
                        )
                        await manager.send_to_session(completion_message.json(), session_id)
                        
                        # Send report data
                        report_message = WebSocketMessage(
                            type="interview_report",
                            session_id=session_id,
                            content=json.dumps(report),
                            timestamp=datetime.now().isoformat()
                        )
                        await manager.send_to_session(report_message.json(), session_id)
                        
                    except Exception as e:
                        error_message = WebSocketMessage(
                            type="error",
                            session_id=session_id,
                            content=f"Error generating report: {str(e)}",
                            timestamp=datetime.now().isoformat()
                        )
                        await manager.send_personal_message(error_message.json(), websocket)
                
            except json.JSONDecodeError:
                # Handle invalid JSON
                error_message = WebSocketMessage(
                    type="error",
                    session_id=session_id,
                    content="Invalid message format. Please send valid JSON.",
                    timestamp=datetime.now().isoformat()
                )
                await manager.send_personal_message(error_message.json(), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        
        # Notify other connections about the disconnect
        disconnect_message = WebSocketMessage(
            type="user_disconnected",
            session_id=session_id,
            content="A user has disconnected from the interview session.",
            timestamp=datetime.now().isoformat()
        )
        await manager.send_to_session(disconnect_message.json(), session_id)

@router.websocket("/ws/recruiter/{recruiter_id}")
async def websocket_recruiter_endpoint(websocket: WebSocket, recruiter_id: str):
    """
    WebSocket endpoint for recruiters to monitor active interviews
    """
    await manager.connect(websocket, f"recruiter_{recruiter_id}")
    
    try:
        # Send welcome message
        welcome_message = WebSocketMessage(
            type="system",
            content="Connected to recruiter dashboard. You'll receive real-time updates.",
            timestamp=datetime.now().isoformat(),
            user_id=recruiter_id
        )
        await manager.send_personal_message(welcome_message.json(), websocket)
        
        while True:
            # Wait for messages (recruiters mainly receive, don't send much)
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                if message_data.get("type") == "get_active_interviews":
                    # Send list of active interviews
                    # This would integrate with your recruiter service
                    active_message = WebSocketMessage(
                        type="active_interviews",
                        content="Active interviews data would go here",
                        timestamp=datetime.now().isoformat(),
                        user_id=recruiter_id
                    )
                    await manager.send_personal_message(active_message.json(), websocket)
                
            except json.JSONDecodeError:
                error_message = WebSocketMessage(
                    type="error",
                    content="Invalid message format.",
                    timestamp=datetime.now().isoformat()
                )
                await manager.send_personal_message(error_message.json(), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"recruiter_{recruiter_id}")

# Helper function to send notifications to recruiters
async def notify_recruiters(message: str, message_type: str = "notification"):
    """
    Send notifications to all connected recruiters
    """
    recruiter_sessions = [key for key in manager.active_connections.keys() 
                         if key.startswith("recruiter_")]
    
    notification = WebSocketMessage(
        type=message_type,
        content=message,
        timestamp=datetime.now().isoformat()
    )
    
    for session in recruiter_sessions:
        await manager.send_to_session(notification.json(), session)