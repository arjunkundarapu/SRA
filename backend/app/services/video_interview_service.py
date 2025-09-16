import asyncio
import json
import base64
import requests
import os
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
import uuid
from dotenv import load_dotenv
from ..database import supabase

load_dotenv()

# Use GEMINI_LIVE_API_KEY first, fallback to GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_LIVE_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash-exp"
GEMINI_REST_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

class VideoInterviewSession:
    def __init__(self, session_id: str, applicant_id: str, resume_data: Optional[Dict] = None):
        self.session_id = session_id
        self.applicant_id = applicant_id
        self.resume_data = resume_data
        self.start_time = datetime.now().isoformat()
        self.status = "active"
        self.conversation_history = []
        self.is_connected = False
        self.interview_context = self._build_interview_context()
        
    def _build_interview_context(self):
        """Build the interview context for the AI"""
        candidate_name = ""
        if self.resume_data and self.resume_data.get('contact_info', {}).get('name'):
            candidate_name = self.resume_data['contact_info']['name']
        
        return f"""You are an AI interviewer conducting a professional video job interview. 
        
        Interview Guidelines:
        1. Act like a human recruiter - be friendly, professional, and engaging
        2. Use the candidate's actual name if provided: {candidate_name if candidate_name else '[Candidate Name]'}
        3. Ask relevant questions based on the candidate's resume
        4. Follow up on answers with deeper questions
        5. Assess technical skills, experience, and cultural fit
        6. Keep the conversation natural and flowing
        7. Be encouraging and positive
        8. Pay attention to both verbal responses and visual cues if images are provided
        9. Provide constructive feedback
        10. Ask one question at a time and wait for responses
        
        Candidate Information:
        Name: {candidate_name if candidate_name else 'Not provided'}
        Resume Summary: {self.resume_data.get('summary', 'No resume provided') if self.resume_data else 'No resume provided'}
        Skills: {', '.join(self.resume_data.get('skills', [])) if self.resume_data else 'Not specified'}
        Experience: {len(self.resume_data.get('experience', [])) if self.resume_data else 0} experience entries found
        
        Start the interview with a professional greeting and your first question.
        """
        
    async def connect_to_gemini(self):
        """Test connection to Gemini API and get initial greeting"""
        try:
            # Check if API key is available
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
            
            print(f"Testing connection to Gemini API with model: {GEMINI_MODEL}")
            
            # Test connection with a simple request
            initial_message = "Please start this video interview with a professional greeting and your first question."
            
            response = await self._call_gemini_api(initial_message)
            
            if response:
                self.is_connected = True
                print("Successfully connected to Gemini API")
                
                # Store the initial AI response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "type": "text"
                })
                
                return True
            else:
                self.is_connected = False
                return False
            
        except Exception as e:
            print(f"Failed to connect to Gemini API: {e}")
            print(f"Error type: {type(e).__name__}")
            self.is_connected = False
            return False
    
    async def _call_gemini_api(self, user_message: str, image_data: Optional[str] = None) -> Optional[str]:
        """Make a call to Gemini REST API"""
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            # Build conversation history for context
            conversation_parts = []
            
            # Add system context
            conversation_parts.append({
                "text": self.interview_context
            })
            
            # Add conversation history (last 5 exchanges to keep context manageable)
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
            
            for msg in recent_history:
                if msg["role"] == "user":
                    conversation_parts.append({"text": f"Candidate: {msg['content']}"})
                elif msg["role"] == "assistant":
                    conversation_parts.append({"text": f"Interviewer: {msg['content']}"})
            
            # Add current user message
            conversation_parts.append({"text": f"Candidate: {user_message}"})
            
            # Add image if provided
            if image_data:
                conversation_parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": image_data
                    }
                })
            
            data = {
                "contents": [{
                    "parts": conversation_parts
                }],
                "generationConfig": {
                    "maxOutputTokens": 500,
                    "temperature": 0.7,
                    "topP": 0.8,
                    "topK": 40
                }
            }
            
            # Make async request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    f"{GEMINI_REST_URL}?key={GEMINI_API_KEY}",
                    headers=headers,
                    json=data,
                    timeout=30
                )
            )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    return content.strip()
                else:
                    print("No valid response from Gemini API")
                    return None
            else:
                print(f"Gemini API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None
    
    async def send_audio_chunk(self, audio_data: bytes):
        """Process audio data (Note: REST API doesn't support real-time audio streaming)"""
        # For now, we'll store audio data but not process it real-time
        # This could be enhanced to convert speech to text first
        print("Audio received but not processed in REST API mode")
        return True
    
    async def send_video_frame(self, video_data: bytes):
        """Send video frame to Gemini API for analysis"""
        if not self.is_connected:
            return False
        
        try:
            # Convert video frame to base64
            video_b64 = base64.b64encode(video_data).decode('utf-8')
            
            # Send to Gemini with request to analyze the video frame
            response = await self._call_gemini_api(
                "Please analyze this video frame from the interview. Comment on the candidate's appearance, body language, and professionalism. Keep it brief.",
                video_b64
            )
            
            if response:
                # Store the analysis
                self.conversation_history.append({
                    "role": "assistant",
                    "content": f"[Video Analysis: {response}]",
                    "timestamp": datetime.now().isoformat(),
                    "type": "video_analysis"
                })
                return True
            
            return False
        except Exception as e:
            print(f"Error sending video frame: {e}")
            return False
    
    async def send_text_message(self, text: str):
        """Send text message to Gemini API"""
        if not self.is_connected:
            return False
        
        try:
            # Store user message
            self.conversation_history.append({
                "role": "user",
                "content": text,
                "timestamp": datetime.now().isoformat(),
                "type": "text"
            })
            
            # Get AI response
            response = await self._call_gemini_api(text)
            
            if response:
                # Store AI response
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                    "type": "text"
                })
                return True
            
            return False
        except Exception as e:
            print(f"Error sending text message: {e}")
            return False
    
    async def get_ai_response(self) -> Optional[Dict]:
        """Get the latest AI response"""
        # Return the last assistant message
        for msg in reversed(self.conversation_history):
            if msg["role"] == "assistant":
                return {
                    "type": "text",
                    "content": msg["content"],
                    "timestamp": msg["timestamp"]
                }
        return None
    
    async def listen_for_responses(self) -> AsyncGenerator[Dict, None]:
        """Get conversation responses (for REST API, this returns stored responses)"""
        # In REST API mode, we don't have real-time streaming
        # Instead, responses are generated on-demand when messages are sent
        # This method can return the conversation history
        for message in self.conversation_history:
            if message["role"] == "assistant":
                yield {
                    "type": message["type"],
                    "content": message["content"],
                    "timestamp": message["timestamp"]
                }
    
    async def end_interview(self):
        """End the interview session"""
        try:
            self.status = "completed"
            self.end_time = datetime.now().isoformat()
            self.is_connected = False
            
            # Update database
            await self._save_session_to_database()
            
            return True
        except Exception as e:
            print(f"Error ending interview: {e}")
            return False
    
    async def _save_session_to_database(self):
        """Save session data to database"""
        try:
            # Save interview session (without interview_type for now)
            session_data = {
                "id": self.session_id,
                "applicant_id": self.applicant_id,
                "start_time": self.start_time,
                "end_time": getattr(self, 'end_time', None),
                "status": self.status,
                "resume_data": json.dumps(self.resume_data) if self.resume_data else None,
                "created_at": datetime.now().isoformat()
            }
            
            # Try to include interview_type if column exists
            try:
                session_data["interview_type"] = "video"
                supabase.table("interview_sessions").upsert(session_data).execute()
            except Exception as db_error:
                # If interview_type column doesn't exist, save without it
                if "interview_type" in str(db_error):
                    print("Warning: interview_type column not found, saving session without it")
                    session_data.pop("interview_type", None)
                    supabase.table("interview_sessions").upsert(session_data).execute()
                else:
                    raise db_error
            
            # Save conversation messages
            for message in self.conversation_history:
                message_data = {
                    "id": str(uuid.uuid4()),
                    "session_id": self.session_id,
                    "role": message["role"],
                    "content": message["content"],
                    "timestamp": message["timestamp"],
                    "created_at": datetime.now().isoformat()
                }
                
                # Try to include message_type if column exists
                try:
                    message_data["message_type"] = message.get("type", "text")
                    supabase.table("interview_messages").insert(message_data).execute()
                except Exception as db_error:
                    # If message_type column doesn't exist, save without it
                    if "message_type" in str(db_error):
                        print("Warning: message_type column not found, saving message without it")
                        message_data.pop("message_type", None)
                        supabase.table("interview_messages").insert(message_data).execute()
                    else:
                        raise db_error
                
        except Exception as e:
            print(f"Error saving session to database: {e}")

# Global session manager
active_video_sessions: Dict[str, VideoInterviewSession] = {}

async def start_video_interview(applicant_id: str, resume_data: Optional[Dict] = None) -> Dict:
    """Start a new video interview session"""
    try:
        session_id = str(uuid.uuid4())
        
        # Create new video interview session
        session = VideoInterviewSession(session_id, applicant_id, resume_data)
        
        # Connect to Gemini Live API
        connection_success = await session.connect_to_gemini()
        
        if not connection_success:
            raise Exception("Failed to connect to Gemini Live API")
        
        # Store session
        active_video_sessions[session_id] = session
        
        # Save initial session to database
        await session._save_session_to_database()
        
        return {
            "session_id": session_id,
            "status": "active",
            "message": "Video interview session started successfully",
            "interview_type": "video"
        }
        
    except Exception as e:
        raise Exception(f"Error starting video interview: {str(e)}")

async def get_video_session(session_id: str) -> Optional[VideoInterviewSession]:
    """Get video interview session by ID"""
    return active_video_sessions.get(session_id)

async def end_video_interview(session_id: str) -> Dict:
    """End a video interview session"""
    try:
        session = active_video_sessions.get(session_id)
        if not session:
            raise Exception("Video interview session not found")
        
        await session.end_interview()
        
        # Remove from active sessions
        del active_video_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": "completed",
            "message": "Video interview ended successfully"
        }
        
    except Exception as e:
        raise Exception(f"Error ending video interview: {str(e)}")

async def generate_video_interview_report(session_id: str) -> Dict:
    """Generate comprehensive report for video interview"""
    try:
        # Get session data from database
        session_response = supabase.table("interview_sessions").select("*").eq("id", session_id).single().execute()
        
        if not session_response.data:
            raise Exception("Interview session not found")
        
        session_data = session_response.data
        
        # Get conversation messages
        messages_response = supabase.table("interview_messages").select("*").eq("session_id", session_id).order("timestamp").execute()
        
        conversation_history = messages_response.data if messages_response.data else []
        
        # Build conversation text for analysis
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in conversation_history if msg.get('message_type') == 'text'
        ])
        
        # Use Gemini API for report generation (using regular API, not Live API)
        from . import interview_service
        
        report_prompt = f"""
        Analyze this VIDEO job interview conversation and provide a comprehensive report.
        
        Interview Type: Video Interview (with audio and visual analysis)
        Interview Conversation:
        {conversation_text}
        
        Please provide a detailed assessment including:
        
        1. **Overall Performance**: Rate the candidate's overall interview performance (1-10)
        2. **Communication Skills**: Assess verbal clarity, articulation, and professionalism
        3. **Visual Presentation**: Evaluate professional appearance, body language, and engagement
        4. **Technical Competency**: Evaluate technical knowledge and skills demonstrated
        5. **Experience Relevance**: How well their experience matches the role
        6. **Cultural Fit**: Assessment of personality and cultural alignment
        7. **Confidence & Presence**: Video-specific assessment of candidate's presence
        8. **Strengths**: Key strengths demonstrated during the video interview
        9. **Areas for Improvement**: Constructive feedback and development areas
        10. **Recommendation**: Hire/Don't Hire with reasoning
        11. **Summary**: Brief overall summary and key takeaways
        
        Note: This was a video interview, so consider both verbal and non-verbal communication aspects.
        Format the response as a professional video interview assessment report.
        """
        
        report_content = interview_service.get_questions(report_prompt)
        
        # Calculate duration
        start_time = datetime.fromisoformat(session_data["start_time"])
        end_time = datetime.fromisoformat(session_data["end_time"]) if session_data.get("end_time") else datetime.now()
        duration = end_time - start_time
        duration_minutes = int(duration.total_seconds() / 60)
        
        # Create report data
        report_data = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "applicant_id": session_data["applicant_id"],
            "report_content": report_content,
            "interview_duration": f"{duration_minutes} minutes",
            "total_questions": len([msg for msg in conversation_history if msg['role'] == 'assistant']),
            "generated_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        # Try to include interview_type if column exists
        try:
            report_data["interview_type"] = "video"
            supabase.table("interview_reports").insert(report_data).execute()
        except Exception as db_error:
            # If interview_type column doesn't exist, save without it
            if "interview_type" in str(db_error):
                print("Warning: interview_type column not found in reports, saving without it")
                report_data.pop("interview_type", None)
                supabase.table("interview_reports").insert(report_data).execute()
            else:
                raise db_error
        
        return report_data
        
    except Exception as e:
        raise Exception(f"Error generating video interview report: {str(e)}")