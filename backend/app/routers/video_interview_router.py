from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, List
import json
import asyncio
import base64
from datetime import datetime
from ..services import video_interview_service
from ..schemas import InterviewStartRequest, APIResponse

router = APIRouter(prefix='/video-interview', tags=["video-interview"])

# Store active WebSocket connections for video interviews
video_connections: Dict[str, List[WebSocket]] = {}

class VideoConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.session_connections: Dict[str, WebSocket] = {}  # Map session_id to websocket

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        self.session_connections[session_id] = websocket

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        if session_id in self.session_connections:
            del self.session_connections[session_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            pass  # Connection might be closed

    async def send_to_session(self, message: str, session_id: str):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Connection might be closed, remove it
                    self.active_connections[session_id].remove(connection)

video_manager = VideoConnectionManager()

@router.post('/start')
async def start_video_interview(request: InterviewStartRequest):
    """Start a new video interview session"""
    try:
        # Convert ResumeData model to dict if provided
        resume_data = request.resume_data.dict() if request.resume_data else None
        
        # Start video interview session
        result = await video_interview_service.start_video_interview(
            request.applicant_id, 
            resume_data
        )
        
        return APIResponse(
            success=True,
            message="Video interview started successfully",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting video interview: {str(e)}")

@router.get('/greeting/{session_id}')
async def get_video_interview_greeting(session_id: str):
    """Get the initial AI greeting for a video interview session"""
    try:
        session = await video_interview_service.get_video_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Video interview session not found")
        
        # Get the latest AI response (the initial greeting)
        ai_response = await session.get_ai_response()
        
        if ai_response:
            return APIResponse(
                success=True,
                message="AI greeting retrieved successfully",
                data={
                    "greeting": ai_response["content"],
                    "timestamp": ai_response["timestamp"],
                    "type": ai_response["type"]
                }
            )
        else:
            # No greeting available yet, return a default one
            default_greeting = "Hello! Welcome to your video interview. I'm your AI interviewer, and I'm excited to learn more about you today. Let's begin!"
            return APIResponse(
                success=True,
                message="Default greeting provided",
                data={
                    "greeting": default_greeting,
                    "timestamp": datetime.now().isoformat(),
                    "type": "text"
                }
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting greeting: {str(e)}")

@router.post('/end/{session_id}')
async def end_video_interview(session_id: str):
    """End a video interview session"""
    try:
        result = await video_interview_service.end_video_interview(session_id)
        
        return APIResponse(
            success=True,
            message="Video interview ended successfully",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ending video interview: {str(e)}")

@router.get('/report/{session_id}')
async def get_video_interview_report(session_id: str):
    """Generate and retrieve video interview report"""
    try:
        report = await video_interview_service.generate_video_interview_report(session_id)
        
        return APIResponse(
            success=True,
            message="Video interview report generated",
            data=report
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.websocket("/ws/{session_id}")
async def video_interview_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time video interview
    Handles audio, video, and text communication with Gemini Live API
    """
    await video_manager.connect(websocket, session_id)
    
    try:
        # Get the video interview session
        session = await video_interview_service.get_video_session(session_id)
        
        if not session:
            await video_manager.send_personal_message(
                json.dumps({
                    "type": "error",
                    "message": "Video interview session not found"
                }), 
                websocket
            )
            return
        
        # Send welcome message
        welcome_message = {
            "type": "connected",
            "session_id": session_id,
            "message": "Connected to video interview session",
            "timestamp": datetime.now().isoformat()
        }
        await video_manager.send_personal_message(json.dumps(welcome_message), websocket)
        
        # Start listening for Gemini responses in background
        gemini_task = asyncio.create_task(listen_to_gemini_responses(session, websocket))
        
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "audio_chunk":
                    # Handle audio data
                    audio_data = base64.b64decode(message_data.get("data", ""))
                    success = await session.send_audio_chunk(audio_data)
                    
                    if not success:
                        await video_manager.send_personal_message(
                            json.dumps({
                                "type": "error",
                                "message": "Failed to send audio to AI"
                            }), 
                            websocket
                        )
                
                elif message_type == "video_frame":
                    # Handle video frame data
                    video_data = base64.b64decode(message_data.get("data", ""))
                    success = await session.send_video_frame(video_data)
                    
                    if not success:
                        await video_manager.send_personal_message(
                            json.dumps({
                                "type": "error",
                                "message": "Failed to send video to AI"
                            }), 
                            websocket
                        )
                
                elif message_type == "text_message":
                    # Handle text message
                    text_content = message_data.get("content", "")
                    success = await session.send_text_message(text_content)
                    
                    if success:
                        # Echo the user message back to confirm receipt
                        user_message = {
                            "type": "user_message",
                            "content": text_content,
                            "timestamp": datetime.now().isoformat()
                        }
                        await video_manager.send_to_session(json.dumps(user_message), session_id)
                    else:
                        await video_manager.send_personal_message(
                            json.dumps({
                                "type": "error",
                                "message": "Failed to send message to AI"
                            }), 
                            websocket
                        )
                
                elif message_type == "ping":
                    # Handle ping for connection health
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }
                    await video_manager.send_personal_message(json.dumps(pong_message), websocket)
                
                elif message_type == "end_interview":
                    # Handle interview completion
                    try:
                        await session.end_interview()
                        
                        # Generate report
                        report = await video_interview_service.generate_video_interview_report(session_id)
                        
                        completion_message = {
                            "type": "interview_completed",
                            "message": "Video interview completed successfully!",
                            "report": report,
                            "timestamp": datetime.now().isoformat()
                        }
                        await video_manager.send_to_session(json.dumps(completion_message), session_id)
                        
                        # Cancel the Gemini listening task
                        gemini_task.cancel()
                        break
                        
                    except Exception as e:
                        error_message = {
                            "type": "error",
                            "message": f"Error ending interview: {str(e)}",
                            "timestamp": datetime.now().isoformat()
                        }
                        await video_manager.send_personal_message(json.dumps(error_message), websocket)
                
                else:
                    # Unknown message type
                    error_message = {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                        "timestamp": datetime.now().isoformat()
                    }
                    await video_manager.send_personal_message(json.dumps(error_message), websocket)
                    
            except json.JSONDecodeError:
                # Handle invalid JSON
                error_message = {
                    "type": "error",
                    "message": "Invalid message format. Please send valid JSON.",
                    "timestamp": datetime.now().isoformat()
                }
                await video_manager.send_personal_message(json.dumps(error_message), websocket)
                
    except WebSocketDisconnect:
        video_manager.disconnect(websocket, session_id)
        
        # Cancel any running tasks
        if 'gemini_task' in locals():
            gemini_task.cancel()
        
        # Notify about disconnect
        disconnect_message = {
            "type": "user_disconnected",
            "message": "User disconnected from video interview",
            "timestamp": datetime.now().isoformat()
        }
        await video_manager.send_to_session(json.dumps(disconnect_message), session_id)
        
    except Exception as e:
        print(f"Video interview WebSocket error: {e}")
        
        # Cancel any running tasks
        if 'gemini_task' in locals():
            gemini_task.cancel()

async def listen_to_gemini_responses(session, websocket: WebSocket):
    """
    Listen for responses from Gemini Live API and forward to client
    """
    try:
        async for response in session.listen_for_responses():
            # Forward Gemini responses to the client
            gemini_message = {
                "type": "ai_response",
                "content_type": response["type"],
                "content": response["content"],
                "timestamp": response["timestamp"]
            }
            
            # Add MIME type for audio responses
            if response["type"] == "audio":
                gemini_message["mime_type"] = response.get("mime_type", "audio/pcm")
            
            await video_manager.send_personal_message(
                json.dumps(gemini_message), 
                websocket
            )
            
    except asyncio.CancelledError:
        print("Gemini response listener cancelled")
    except Exception as e:
        print(f"Error listening to Gemini responses: {e}")
        
        # Send error to client
        error_message = {
            "type": "ai_error",
            "message": f"AI connection error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        await video_manager.send_personal_message(json.dumps(error_message), websocket)