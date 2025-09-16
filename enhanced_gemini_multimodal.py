#!/usr/bin/env python3
"""
Enhanced Gemini Multimodal Video Interview System
Demonstrates advanced audio and video processing with Gemini API
"""

import asyncio
import base64
import json
import os
import requests
import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_LIVE_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash-exp"  # Supports multimodal
GEMINI_REST_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

class EnhancedGeminiMultimodal:
    """Enhanced Gemini integration for audio and video processing"""
    
    def __init__(self):
        self.conversation_history = []
        self.video_analysis_history = []
        self.audio_context = []
        
    async def process_multimodal_interview_data(
        self, 
        text_input: str,
        video_frame: Optional[bytes] = None,
        audio_transcript: Optional[str] = None,
        interview_context: Optional[str] = None
    ) -> Dict:
        """
        Process combined text, video, and audio data for comprehensive interview analysis
        """
        try:
            # Build comprehensive multimodal prompt
            parts = []
            
            # Add interview context
            if interview_context:
                parts.append({
                    "text": f"Interview Context: {interview_context}\n\n"
                })
            
            # Add conversation history for context
            if self.conversation_history:
                recent_history = self.conversation_history[-5:]  # Last 5 exchanges
                history_text = "Recent Conversation:\n"
                for msg in recent_history:
                    history_text += f"{msg['role']}: {msg['content'][:100]}...\n"
                parts.append({"text": history_text + "\n"})
            
            # Add current text input
            parts.append({
                "text": f"Current Response: {text_input}\n\n"
            })
            
            # Add audio transcript if available
            if audio_transcript:
                parts.append({
                    "text": f"Audio Transcript: {audio_transcript}\n\n"
                })
            
            # Add video frame for analysis
            if video_frame:
                video_b64 = base64.b64encode(video_frame).decode('utf-8')
                parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": video_b64
                    }
                })
                parts.append({
                    "text": "Please analyze the video frame above along with the text response."
                })
            
            # Add comprehensive analysis prompt
            analysis_prompt = """
            Based on the multimodal data provided (text, audio transcript, and video frame), please provide:
            
            1. **Content Analysis**: Evaluate the substance and relevance of the response
            2. **Communication Skills**: Assess verbal clarity and articulation
            3. **Visual Presentation**: Analyze body language, professionalism, and engagement
            4. **Overall Assessment**: Provide a holistic evaluation
            5. **Next Question**: Generate an appropriate follow-up question
            
            Keep your analysis professional and constructive.
            """
            parts.append({"text": analysis_prompt})
            
            # Make API call
            response_data = await self._call_gemini_multimodal_api(parts)
            
            if response_data:
                # Store analysis
                analysis = {
                    "timestamp": datetime.now().isoformat(),
                    "input_text": text_input,
                    "has_video": video_frame is not None,
                    "has_audio": audio_transcript is not None,
                    "analysis": response_data,
                    "type": "multimodal_analysis"
                }
                
                self.conversation_history.append(analysis)
                
                return {
                    "success": True,
                    "analysis": response_data,
                    "type": "multimodal",
                    "timestamp": analysis["timestamp"]
                }
            
            return {"success": False, "error": "No response from Gemini"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def analyze_video_sequence(
        self, 
        video_frames: List[bytes], 
        duration_seconds: int,
        context: str = ""
    ) -> Dict:
        """
        Analyze a sequence of video frames for behavioral patterns
        """
        try:
            parts = []
            
            # Add context
            parts.append({
                "text": f"Video Sequence Analysis ({duration_seconds} seconds)\n"
                       f"Context: {context}\n\n"
                       f"Analyzing {len(video_frames)} frames for behavioral patterns:\n"
            })
            
            # Add multiple frames for temporal analysis
            for i, frame in enumerate(video_frames[:5]):  # Limit to 5 frames for API efficiency
                frame_b64 = base64.b64encode(frame).decode('utf-8')
                parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": frame_b64
                    }
                })
                parts.append({
                    "text": f"Frame {i+1}/{len(video_frames)} (timestamp: {i * duration_seconds / len(video_frames):.1f}s)\n"
                })
            
            # Add analysis prompt
            analysis_prompt = """
            Please analyze these video frames for:
            
            1. **Consistency**: Does the candidate maintain professional posture?
            2. **Engagement**: How does their engagement level change over time?
            3. **Nervousness Indicators**: Any signs of anxiety or discomfort?
            4. **Confidence Patterns**: Changes in confidence throughout the sequence?
            5. **Overall Impression**: Professional presentation assessment
            
            Provide insights based on the temporal progression shown in the frames.
            """
            parts.append({"text": analysis_prompt})
            
            response_data = await self._call_gemini_multimodal_api(parts)
            
            if response_data:
                analysis = {
                    "timestamp": datetime.now().isoformat(),
                    "frame_count": len(video_frames),
                    "duration": duration_seconds,
                    "analysis": response_data,
                    "type": "video_sequence_analysis"
                }
                
                self.video_analysis_history.append(analysis)
                
                return {
                    "success": True,
                    "analysis": response_data,
                    "type": "video_sequence",
                    "timestamp": analysis["timestamp"]
                }
            
            return {"success": False, "error": "No response from Gemini"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def analyze_audio_patterns(
        self, 
        audio_transcripts: List[str], 
        timestamps: List[str],
        context: str = ""
    ) -> Dict:
        """
        Analyze audio/speech patterns across multiple responses
        """
        try:
            # Build comprehensive audio analysis prompt
            parts = []
            
            parts.append({
                "text": f"Audio Pattern Analysis\n"
                       f"Context: {context}\n\n"
                       f"Analyzing {len(audio_transcripts)} audio transcripts:\n\n"
            })
            
            # Add each transcript with timestamp
            for i, (transcript, timestamp) in enumerate(zip(audio_transcripts, timestamps)):
                parts.append({
                    "text": f"Response {i+1} ({timestamp}):\n"
                           f'"{transcript}"\n\n'
                })
            
            # Add analysis prompt
            analysis_prompt = """
            Based on these audio transcripts, please analyze:
            
            1. **Communication Clarity**: How clear and articulate is the candidate?
            2. **Language Proficiency**: Professional language usage and vocabulary
            3. **Response Patterns**: Consistency in communication style
            4. **Confidence Indicators**: Evidence of confidence or uncertainty in speech
            5. **Professional Tone**: Appropriateness for interview context
            6. **Improvement Areas**: Constructive feedback for communication enhancement
            
            Provide detailed insights about the candidate's verbal communication skills.
            """
            parts.append({"text": analysis_prompt})
            
            response_data = await self._call_gemini_multimodal_api(parts)
            
            if response_data:
                analysis = {
                    "timestamp": datetime.now().isoformat(),
                    "transcript_count": len(audio_transcripts),
                    "analysis": response_data,
                    "type": "audio_pattern_analysis"
                }
                
                self.audio_context.append(analysis)
                
                return {
                    "success": True,
                    "analysis": response_data,
                    "type": "audio_patterns",
                    "timestamp": analysis["timestamp"]
                }
            
            return {"success": False, "error": "No response from Gemini"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_comprehensive_report(self) -> Dict:
        """
        Generate a comprehensive interview report using all multimodal data
        """
        try:
            parts = []
            
            # Add report header
            parts.append({
                "text": "COMPREHENSIVE MULTIMODAL INTERVIEW REPORT\n"
                       "=" * 50 + "\n\n"
            })
            
            # Add conversation summary
            if self.conversation_history:
                parts.append({
                    "text": f"Interview Summary:\n"
                           f"- Total interactions: {len(self.conversation_history)}\n"
                           f"- Multimodal analyses: {len([m for m in self.conversation_history if m.get('type') == 'multimodal_analysis'])}\n\n"
                           f"Key Response Highlights:\n"
                })
                
                for i, msg in enumerate(self.conversation_history[-5:], 1):
                    if msg.get('input_text'):
                        parts.append({
                            "text": f"{i}. {msg['input_text'][:100]}...\n"
                        })
            
            # Add video analysis summary
            if self.video_analysis_history:
                parts.append({
                    "text": f"\nVideo Analysis Summary:\n"
                           f"- Video sequences analyzed: {len(self.video_analysis_history)}\n\n"
                })
            
            # Add audio analysis summary
            if self.audio_context:
                parts.append({
                    "text": f"\nAudio Analysis Summary:\n"
                           f"- Audio patterns analyzed: {len(self.audio_context)}\n\n"
                })
            
            # Add comprehensive report prompt
            report_prompt = """
            Based on all the multimodal data collected during this interview, please generate a comprehensive report including:
            
            📊 **OVERALL PERFORMANCE RATING** (1-10 scale)
            - Communication Skills
            - Technical Competency
            - Visual Presentation
            - Professional Demeanor
            - Cultural Fit
            
            💬 **DETAILED ANALYSIS**
            - Strengths demonstrated
            - Areas for improvement
            - Interview highlights
            - Recommendation (Hire/No Hire/Additional Interview)
            
            🎯 **SPECIFIC FEEDBACK**
            - Communication effectiveness
            - Professional presentation
            - Technical knowledge demonstration
            - Interview performance consistency
            
            📝 **INTERVIEWER NOTES**
            - Key observations
            - Memorable responses
            - Overall impression
            
            Please provide a thorough, professional assessment suitable for HR review.
            """
            parts.append({"text": report_prompt})
            
            response_data = await self._call_gemini_multimodal_api(parts)
            
            if response_data:
                return {
                    "success": True,
                    "report": response_data,
                    "type": "comprehensive_report",
                    "timestamp": datetime.now().isoformat(),
                    "data_summary": {
                        "total_interactions": len(self.conversation_history),
                        "video_analyses": len(self.video_analysis_history),
                        "audio_analyses": len(self.audio_context)
                    }
                }
            
            return {"success": False, "error": "No response from Gemini"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _call_gemini_multimodal_api(self, parts: List[Dict]) -> Optional[str]:
        """Make a multimodal API call to Gemini"""
        try:
            headers = {"Content-Type": "application/json"}
            
            data = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "maxOutputTokens": 1000,
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
                    timeout=45  # Longer timeout for multimodal
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
            print(f"Error calling Gemini multimodal API: {e}")
            return None

# Utility functions for video processing
def extract_video_frames(video_path: str, max_frames: int = 10) -> List[bytes]:
    """Extract frames from video for analysis"""
    frames = []
    try:
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(1, frame_count // max_frames)
        
        frame_idx = 0
        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_idx % interval == 0:
                # Resize frame for efficiency
                frame = cv2.resize(frame, (640, 480))
                # Convert to JPEG bytes
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                frames.append(buffer.tobytes())
            
            frame_idx += 1
        
        cap.release()
        return frames
        
    except Exception as e:
        print(f"Error extracting video frames: {e}")
        return []

def capture_live_frame() -> Optional[bytes]:
    """Capture a single frame from camera"""
    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            cap.release()
            return buffer.tobytes()
        cap.release()
        return None
    except Exception as e:
        print(f"Error capturing frame: {e}")
        return None

# Example usage and testing
async def demo_enhanced_multimodal():
    """Demonstrate enhanced multimodal capabilities"""
    print("🎥 Enhanced Gemini Multimodal Video Interview Demo")
    print("=" * 50)
    
    if not GEMINI_API_KEY:
        print("❌ No Gemini API key found")
        return
    
    gemini = EnhancedGeminiMultimodal()
    
    # Demo 1: Multimodal analysis with text and video
    print("\n🧪 Demo 1: Multimodal Text + Video Analysis")
    frame = capture_live_frame()
    if frame:
        result = await gemini.process_multimodal_interview_data(
            text_input="I have 5 years of experience in Python development and machine learning.",
            video_frame=frame,
            interview_context="Software Engineer position interview"
        )
        if result["success"]:
            print("✅ Multimodal analysis completed!")
            print(f"Analysis: {result['analysis'][:200]}...")
    
    # Demo 2: Audio pattern analysis
    print("\n🧪 Demo 2: Audio Pattern Analysis")
    sample_transcripts = [
        "I have extensive experience with Python and machine learning frameworks.",
        "In my previous role, I led a team of five developers on a major project.",
        "I'm passionate about artificial intelligence and its applications in business."
    ]
    sample_timestamps = [
        "2024-01-15 10:30:00",
        "2024-01-15 10:32:30", 
        "2024-01-15 10:35:15"
    ]
    
    audio_result = await gemini.analyze_audio_patterns(
        audio_transcripts=sample_transcripts,
        timestamps=sample_timestamps,
        context="Technical interview for Senior Developer position"
    )
    
    if audio_result["success"]:
        print("✅ Audio pattern analysis completed!")
        print(f"Analysis: {audio_result['analysis'][:200]}...")
    
    # Demo 3: Comprehensive report
    print("\n🧪 Demo 3: Comprehensive Report Generation")
    report = await gemini.generate_comprehensive_report()
    if report["success"]:
        print("✅ Comprehensive report generated!")
        print(f"Report: {report['report'][:300]}...")
    
    print("\n🎉 Enhanced multimodal demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_enhanced_multimodal())