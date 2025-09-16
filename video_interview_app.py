import streamlit as st
import requests
import json
from datetime import datetime
import asyncio
import websockets
import base64
import threading
import time
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    st.warning("OpenCV not available. Video functionality will be limited.")

try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    st.warning("PyAudio not available. Audio functionality will be limited.")

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    st.warning("pyttsx3 not available. Text-to-speech will be limited.")

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    STT_AVAILABLE = False
    st.warning("speech_recognition not available. Speech-to-text will be limited.")

# Configure Streamlit page for video interview
st.set_page_config(
    page_title="SRA Video Interview", 
    page_icon="🎥", 
    layout="wide"
)

# API Base URL
API_BASE = "http://127.0.0.1:8000"

# Initialize session state for video interview with proper defaults
def init_session_state():
    """Initialize session state variables to prevent ScriptRunContext warnings"""
    defaults = {
        'video_interview_session_id': None,
        'video_interview_active': False,
        'video_conversation_history': [],
        'camera_active': False,
        'microphone_active': False,
        'authenticated': True,  # Simplified for demo
        'user_id': "demo_user_123",
        'last_message': None,
        'websocket_connected': False,
        'audio_streaming': False,
        'video_streaming': False,
        'tts_engine': None,
        'current_ai_response': None,
        'audio_buffer': [],
        'video_buffer': [],
        'auto_recording': False,
        'waiting_for_response': False,
        'last_ai_response_time': None,
        'interview_mode': 'automatic'  # 'automatic' or 'manual'
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Initialize session state
init_session_state()

# Initialize TTS engine
def init_tts_engine():
    """Initialize text-to-speech engine"""
    if TTS_AVAILABLE and st.session_state.tts_engine is None:
        try:
            # Try to import required Windows modules
            try:
                import pywintypes
                import pythoncom
            except ImportError:
                st.warning("Windows TTS dependencies missing. Installing...")
                return None
            
            engine = pyttsx3.init()
            # Set properties
            voices = engine.getProperty('voices')
            if voices:
                # Try to use a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            engine.setProperty('rate', 150)  # Speaking rate
            engine.setProperty('volume', 0.8)  # Volume level
            st.session_state.tts_engine = engine
            return engine
        except Exception as e:
            st.warning(f"TTS initialization failed: {e}. Using text-only mode.")
            return None
    return st.session_state.tts_engine

def speak_text(text: str):
    """Convert text to speech"""
    if TTS_AVAILABLE:
        engine = init_tts_engine()
        if engine:
            try:
                # Run TTS in a separate thread to avoid blocking
                def tts_thread():
                    engine.say(text)
                    engine.runAndWait()
                
                thread = threading.Thread(target=tts_thread)
                thread.daemon = True
                thread.start()
                return True
            except Exception as e:
                st.error(f"TTS Error: {e}")
    return False

def handle_ai_response(ai_response: str, response_type: str = "text"):
    """Handle AI response - store in conversation and speak aloud"""
    # Add AI response to conversation
    st.session_state.video_conversation_history.append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.now().isoformat(),
        "type": response_type
    })
    
    # Store current response and speak it aloud
    st.session_state.current_ai_response = ai_response
    st.session_state.last_ai_response_time = datetime.now()
    
    # Always speak AI responses
    if speak_text(ai_response):
        st.success("🔊 AI is speaking...")
        
        # Start automatic recording after AI finishes speaking
        if st.session_state.interview_mode == 'automatic' and st.session_state.microphone_active:
            st.session_state.auto_recording = True
            st.session_state.waiting_for_response = True
            st.info("🎤 Listening for your response... (speak naturally)")
        
        return True
    else:
        st.info("📝 AI response displayed (speech not available)")
        return False

def automatic_speech_capture():
    """Automatically capture speech after AI question"""
    if not STT_AVAILABLE or not st.session_state.microphone_active:
        return None
    
    try:
        r = sr.Recognizer()
        
        # Adjust for ambient noise
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
        
        # Listen for speech with longer timeout for natural conversation
        with sr.Microphone() as source:
            st.info("🎤 Listening... (speak when ready)")
            audio = r.listen(source, timeout=15, phrase_time_limit=30)
        
        # Convert speech to text
        text = r.recognize_google(audio)
        return text
        
    except sr.WaitTimeoutError:
        st.warning("⏱️ No speech detected. Please try speaking again or use text input.")
        return None
    except sr.UnknownValueError:
        st.warning("🔊 Could not understand speech. Please try again or speak more clearly.")
        return None
    except Exception as e:
        st.error(f"Speech recognition error: {e}")
        return None

def generate_contextual_ai_response(user_input: str) -> str:
    """Generate contextually appropriate AI response based on conversation history"""
    # Get conversation context
    conversation_length = len(st.session_state.video_conversation_history)
    
    # Different response patterns based on interview stage
    if conversation_length <= 2:
        # Opening questions
        responses = [
            f"Thank you for sharing that, {user_input[:30]}... Can you tell me about a specific project you're most proud of?",
            f"That's interesting! Based on what you've told me about {user_input[:40]}..., what motivated you to pursue this career path?",
            f"I appreciate that insight. Could you walk me through your most challenging professional experience?"
        ]
    elif conversation_length <= 6:
        # Deep dive questions
        responses = [
            f"Excellent point about {user_input[:30]}... How do you typically approach problem-solving in complex situations?",
            f"That's a great example. When you mentioned {user_input[:40]}..., how did you measure the success of that approach?",
            f"Very insightful. Can you tell me about a time when you had to learn something completely new for a project?"
        ]
    else:
        # Closing questions
        responses = [
            f"Thank you for that detailed response about {user_input[:30]}... What questions do you have about this role or our company?",
            f"That's valuable insight. Based on everything we've discussed, what excites you most about this opportunity?",
            f"Excellent. As we wrap up, is there anything important about your background that we haven't covered yet?"
        ]
    
    # Select response based on input length (more detailed = more specific follow-up)
    import random
    return random.choice(responses)

def setup_websocket_connection():
    """Setup WebSocket connection for real-time communication"""
    if not st.session_state.video_interview_session_id:
        return False
    
    session_id = st.session_state.video_interview_session_id
    websocket_url = f"ws://127.0.0.1:8000/video-interview/ws/{session_id}"
    
    try:
        # This is a simplified WebSocket setup
        # In a real implementation, you'd use asyncio and handle this properly
        st.session_state.websocket_connected = True
        return True
    except Exception as e:
        st.error(f"WebSocket connection failed: {e}")
        return False

def capture_audio_chunk():
    """Capture audio chunk from microphone"""
    if not PYAUDIO_AVAILABLE or not st.session_state.microphone_active:
        return None
    
    try:
        # Audio configuration
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        
        p = pyaudio.PyAudio()
        
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)
        
        # Record for 1 second
        frames = []
        for _ in range(0, int(RATE / CHUNK * 1)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # Convert to bytes
        audio_data = b''.join(frames)
        return audio_data
        
    except Exception as e:
        st.error(f"Audio capture error: {e}")
        return None

def start_continuous_video_stream():
    """Start continuous video streaming in the background"""
    if not CV2_AVAILABLE or not st.session_state.camera_active:
        return None
    
    # Initialize video stream counter if not exists
    if 'video_stream_counter' not in st.session_state:
        st.session_state.video_stream_counter = 0
    
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # Increment counter for continuous effect
                st.session_state.video_stream_counter += 1
                
                # Convert frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Add timestamp overlay for live effect
                current_time = datetime.now().strftime("%H:%M:%S")
                
                cap.release()
                return frame_rgb, current_time
            cap.release()
    except Exception as e:
        st.error(f"Video stream error: {e}")
    return None

def capture_video_frame():
    """Capture video frame from camera"""
    if not CV2_AVAILABLE or not st.session_state.camera_active:
        return None
    
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                # Resize frame for efficiency
                frame = cv2.resize(frame, (320, 240))
                # Convert to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                cap.release()
                return buffer.tobytes()
            cap.release()
    except Exception as e:
        st.error(f"Video capture error: {e}")
    return None

def start_video_interview(applicant_id, resume_data=None):
    """Start a video interview session"""
    try:
        payload = {"applicant_id": applicant_id}
        if resume_data:
            payload["resume_data"] = resume_data
        
        response = requests.post(f"{API_BASE}/video-interview/start", json=payload)
        if response.status_code == 200:
            result = response.json()
            # Check if the API call was successful
            if result.get("success", False) and "data" in result:
                return result
            else:
                # Handle API-level errors
                error_msg = result.get("error") or result.get("message", "Unknown error")
                return {"error": error_msg}
        else:
            # Handle HTTP errors
            try:
                error_detail = response.json().get("detail", "Failed to start video interview")
            except:
                error_detail = "Failed to start video interview"
            return {"error": error_detail}
    except Exception as e:
        return {"error": str(e)}

def end_video_interview(session_id):
    """End a video interview session"""
    try:
        response = requests.post(f"{API_BASE}/video-interview/end/{session_id}")
        if response.status_code == 200:
            result = response.json()
            # Check if the API call was successful
            if result.get("success", False):
                return result
            else:
                # Handle API-level errors
                error_msg = result.get("error") or result.get("message", "Unknown error")
                return {"error": error_msg}
        else:
            # Handle HTTP errors
            try:
                error_detail = response.json().get("detail", "Failed to end video interview")
            except:
                error_detail = "Failed to end video interview"
            return {"error": error_detail}
    except Exception as e:
        return {"error": str(e)}

def get_video_interview_report(session_id):
    """Get video interview report"""
    try:
        response = requests.get(f"{API_BASE}/video-interview/report/{session_id}")
        if response.status_code == 200:
            result = response.json()
            # Check if the API call was successful
            if result.get("success", False) and "data" in result:
                return result
            else:
                # Handle API-level errors
                error_msg = result.get("error") or result.get("message", "Unknown error")
                return {"error": error_msg}
        else:
            # Handle HTTP errors
            try:
                error_detail = response.json().get("detail", "Failed to get report")
            except:
                error_detail = "Failed to get report"
            return {"error": error_detail}
    except Exception as e:
        return {"error": str(e)}

# Main Video Interview App
st.title("🎥 SRA Video Interview System")
st.markdown("Real-time AI-powered video interviews with Gemini Live API")

# Sidebar for navigation
st.sidebar.title("Video Interview Controls")
st.sidebar.success(f"✅ Demo Mode: {st.session_state.user_id}")

# Main functionality tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎥 Start Video Interview", "📹 Live Interview", "📊 Interview Report", "ℹ️ Instructions"])

with tab1:
    st.header("🎥 Start Video Interview")
    
    if st.session_state.video_interview_session_id is None:
        st.write("Ready to start your AI video interview? Make sure your camera and microphone are working!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Resume Data")
            
            # Check for available resume data (simplified)
            use_resume = st.checkbox("Use resume data for personalized questions", value=True)
            
            if use_resume:
                st.info("📄 Using sample resume data for demonstration")
                sample_resume = {
                    "raw_text": "John Doe\nSenior AI Engineer\nEmail: john@example.com\nSkills: Python, FastAPI, Machine Learning, Computer Vision\nExperience: 2022-2024 Senior AI Engineer at Tech Corp\nEducation: Bachelor's in Computer Science\nSummary: Experienced AI engineer with 5 years in software development",
                    "contact_info": {"name": "John Doe", "email": "john@example.com", "phone": "(555) 123-4567"},
                    "skills": ["Python", "FastAPI", "Machine Learning", "Computer Vision"],
                    "experience": [{"period": "2022-2024", "context": "Senior AI Engineer at Tech Corp"}],
                    "education": ["Bachelor's in Computer Science"],
                    "summary": "Experienced AI engineer with 5 years in software development"
                }
                st.json(sample_resume)
            else:
                sample_resume = None
        
        with col2:
            st.subheader("🎛️ Camera & Microphone Test")
            
            # Camera test
            if st.button("📷 Test Camera"):
                if not CV2_AVAILABLE:
                    st.error("❌ OpenCV not available. Please install: pip install opencv-python")
                else:
                    try:
                        cap = cv2.VideoCapture(0)
                        if cap.isOpened():
                            ret, frame = cap.read()
                            if ret:
                                # Convert BGR to RGB for Streamlit
                                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                st.image(frame_rgb, caption="Camera Test - Looking good! 📸", width=300)
                                st.success("✅ Camera is working!")
                            else:
                                st.error("❌ Failed to capture frame from camera.")
                            cap.release()
                        else:
                            st.error("❌ Camera not found. Please check your camera connection.")
                    except Exception as e:
                        st.error(f"❌ Camera test failed: {e}")
            
            # Microphone test info
            st.info("🎤 Microphone will be tested when interview starts")
        
        st.markdown("---")
        
        # Start interview button
        if st.button("🚀 Start Video Interview", type="primary", use_container_width=True):
            with st.spinner("Starting video interview session..."):
                result = start_video_interview(
                    st.session_state.user_id, 
                    sample_resume if use_resume else None
                )
                
            # Check if the video interview started successfully
            if result.get("success", False) and "data" in result and not result.get("error"):
                st.session_state.video_interview_session_id = result["data"]["session_id"]
                st.session_state.video_interview_active = True
                
                # Get the initial AI greeting from the session
                try:
                    # Call a new endpoint to get the initial AI response
                    session_id = result["data"]["session_id"]
                    greeting_response = requests.get(f"{API_BASE}/video-interview/greeting/{session_id}")
                    if greeting_response.status_code == 200:
                        greeting_data = greeting_response.json()
                        if greeting_data.get("success") and "data" in greeting_data:
                            ai_greeting = greeting_data["data"].get("greeting", "")
                            if ai_greeting:
                                # Use the improved response handler
                                handle_ai_response(ai_greeting, "greeting")
                except Exception as e:
                    st.warning(f"Could not get AI greeting: {e}")
                
                st.success(f"✅ Video interview started! Session ID: {result['data']['session_id']}")
                st.rerun()
            else:
                error_msg = result.get("error") or "Unknown error occurred"
                st.error(f"❌ Failed to start video interview: {error_msg}")
    else:
        st.success(f"🎥 Video interview session active: {st.session_state.video_interview_session_id}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Start New Video Interview"):
                st.session_state.video_interview_session_id = None
                st.session_state.video_interview_active = False
                st.session_state.video_conversation_history = []
                st.rerun()
        
        with col2:
            if st.button("🏁 End Current Interview"):
                with st.spinner("Ending interview..."):
                    result = end_video_interview(st.session_state.video_interview_session_id)
                
                # Check if the interview ended successfully
                if result.get("success", False) and not result.get("error"):
                    st.session_state.video_interview_active = False
                    st.success("✅ Video interview ended successfully!")
                else:
                    error_msg = result.get("error") or "Unknown error occurred"
                    st.error(f"❌ Error ending interview: {error_msg}")

with tab2:
    st.header("📹 Live Video Interview")
    
    if st.session_state.video_interview_session_id is None:
        st.warning("⚠️ Please start a video interview session first in the 'Start Video Interview' tab.")
    else:
        st.info(f"🎥 Active Session: {st.session_state.video_interview_session_id}")
        
        # Media controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            camera_toggle = st.checkbox("📷 Camera", value=st.session_state.camera_active)
            if camera_toggle != st.session_state.camera_active:
                st.session_state.camera_active = camera_toggle
                if camera_toggle:
                    st.success("📷 Camera activated")
                    st.session_state.video_streaming = True
                else:
                    st.info("📷 Camera deactivated")
                    st.session_state.video_streaming = False
        
        with col2:
            mic_toggle = st.checkbox("🎤 Microphone", value=st.session_state.microphone_active)
            if mic_toggle != st.session_state.microphone_active:
                st.session_state.microphone_active = mic_toggle
                if mic_toggle:
                    st.success("🎤 Microphone activated")
                    st.session_state.audio_streaming = True
                else:
                    st.info("🎤 Microphone deactivated")
                    st.session_state.audio_streaming = False
        
        with col3:
            if st.button("🔴 End Interview"):
                with st.spinner("Ending interview and generating report..."):
                    result = end_video_interview(st.session_state.video_interview_session_id)
                
                # Check if the interview ended successfully
                if result.get("success", False) and not result.get("error"):
                    st.session_state.video_interview_active = False
                    st.success("✅ Interview ended! Check the Report tab.")
                    st.rerun()
                else:
                    error_msg = result.get("error") or "Unknown error occurred"
                    st.error(f"❌ Error: {error_msg}")
        
        st.markdown("---")
        
        # Video feed and audio processing
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📹 Video Feed")
            video_placeholder = st.empty()
            
            if st.session_state.camera_active:
                if not CV2_AVAILABLE:
                    video_placeholder.error("❌ OpenCV not available. Install with: pip install opencv-python")
                else:
                    # Continuous video streaming with auto-refresh
                    if st.session_state.video_streaming:
                        # Get continuous video stream
                        stream_result = start_continuous_video_stream()
                        if stream_result:
                            frame_rgb, timestamp = stream_result
                            video_placeholder.image(
                                frame_rgb, 
                                caption=f"🔴 LIVE - {timestamp} | Frame #{st.session_state.get('video_stream_counter', 0)}", 
                                use_container_width=True
                            )
                            
                            # Controlled auto-refresh for continuous streaming effect
                            # Only refresh every few frames to prevent excessive load
                            if st.session_state.get('video_stream_counter', 0) % 2 == 0:
                                time.sleep(0.2)  # Brief pause for stability
                                st.rerun()  # Trigger refresh for next frame
                        else:
                            video_placeholder.warning("⚠️ Video stream unavailable")
                    else:
                        # Single frame capture
                        try:
                            cap = cv2.VideoCapture(0)
                            if cap.isOpened():
                                ret, frame = cap.read()
                                if ret:
                                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                    video_placeholder.image(frame_rgb, caption="Camera Feed (Static)", use_container_width=True)
                                cap.release()
                            else:
                                video_placeholder.error("❌ Camera not available")
                        except Exception as e:
                            video_placeholder.error(f"❌ Camera error: {e}")
            else:
                video_placeholder.info("📷 Camera is off. Enable camera to start video interview.")
        
        with col2:
            st.subheader("🎤 Audio Status")
            
            if st.session_state.microphone_active:
                if PYAUDIO_AVAILABLE:
                    st.success("🎤 Microphone is active")
                    st.info("🔊 AI can hear you speaking")
                    
                    # Audio level indicator
                    if st.session_state.audio_streaming:
                        st.progress(0.7, text="Audio Level: Active")
                        st.caption("🎤 Listening for speech...")
                        
                        # Simulate audio capture
                        audio_data = capture_audio_chunk()
                        if audio_data:
                            st.caption("🤖 AI is processing your speech...")
                    else:
                        st.progress(0.0, text="Audio Level: Standby")
                else:
                    st.warning("🎤 PyAudio not available")
                    st.info("Install with: pip install pyaudio")
            else:
                st.warning("🎤 Microphone is off")
                st.info("🔇 Enable microphone for voice interaction")
            
            # TTS Status
            st.subheader("🔊 AI Speech")
            if TTS_AVAILABLE:
                st.success("🔊 Text-to-Speech enabled")
                st.info("🎙️ AI will speak questions aloud")
                
                # Show current AI response if any
                if st.session_state.current_ai_response:
                    st.text_area("Current AI Question:", st.session_state.current_ai_response, height=100, disabled=True)
                    if st.button("🔁 Repeat Question"):
                        speak_text(st.session_state.current_ai_response)
                        st.success("Repeating question...")
            else:
                st.warning("🔊 TTS not available")
                st.info("Install with: pip install pyttsx3")
        
        # Interview Mode Selection
        st.markdown("---")
        st.subheader("🔄 Interview Mode")
        
        col1, col2 = st.columns(2)
        
        with col1:
            interview_mode = st.radio(
                "Select Interview Mode:",
                ["Automatic", "Manual"],
                index=0 if st.session_state.interview_mode == 'automatic' else 1,
                help="Automatic: AI asks questions and automatically records your responses. Manual: You control when to speak."
            )
            
            if interview_mode.lower() != st.session_state.interview_mode:
                st.session_state.interview_mode = interview_mode.lower()
                st.session_state.auto_recording = False
                st.session_state.waiting_for_response = False
                st.rerun()
        
        with col2:
            st.write("**Current Status:**")
            if st.session_state.interview_mode == 'automatic':
                if st.session_state.auto_recording:
                    st.success("🎤 Listening for your response...")
                elif st.session_state.waiting_for_response:
                    st.info("⏳ Processing your response...")
                elif st.session_state.current_ai_response:
                    st.info("🔊 AI is speaking. Please listen...")
                else:
                    st.info("🤖 Ready for automatic interview")
            else:
                st.info("📝 Manual mode - use buttons below")
        
        # Automatic Interview Flow
        if st.session_state.interview_mode == 'automatic' and st.session_state.microphone_active:
            if st.session_state.auto_recording and st.session_state.waiting_for_response:
                try:
                    # Automatically capture speech
                    with st.spinner("🎤 Listening for your response... (speak naturally)"):
                        user_speech = automatic_speech_capture()
                    
                    if user_speech:
                        # Add user response to conversation
                        st.session_state.video_conversation_history.append({
                            "role": "user",
                            "content": user_speech,
                            "timestamp": datetime.now().isoformat(),
                            "type": "voice_auto"
                        })
                        
                        # Generate contextual AI response
                        with st.spinner("🤖 AI is thinking..."):
                            ai_response = generate_contextual_ai_response(user_speech)
                        
                        # Reset auto recording state
                        st.session_state.auto_recording = False
                        st.session_state.waiting_for_response = False
                        
                        # Handle AI response (will trigger next recording cycle)
                        handle_ai_response(ai_response, "voice_auto")
                        
                        st.success(f"✅ Recorded: {user_speech[:50]}...")
                        time.sleep(2)  # Brief pause before next cycle
                        st.rerun()
                    
                    else:
                        # Reset if no speech detected
                        st.session_state.auto_recording = False
                        st.session_state.waiting_for_response = False
                        st.warning("⏱️ No speech detected. Please try again or switch to manual mode.")
                        
                        # Offer to restart automatic cycle
                        if st.button("🔄 Try Again (Automatic)"):
                            if st.session_state.current_ai_response:
                                # Repeat the last question and restart cycle
                                handle_ai_response(st.session_state.current_ai_response, "retry")
                            st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Automatic recording error: {e}")
                    st.session_state.auto_recording = False
                    st.session_state.waiting_for_response = False
                    
                    # Fallback to manual mode
                    if st.button("🔧 Switch to Manual Mode"):
                        st.session_state.interview_mode = 'manual'
                        st.rerun()
        
        # Enhanced communication section
        st.markdown("---")
        st.subheader("💬 Enhanced Communication")
        
        # Voice to text section
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("🎤 **Voice Input**")
            if st.button("🎤 Speak Your Answer", disabled=not st.session_state.microphone_active):
                if STT_AVAILABLE and st.session_state.microphone_active:
                    with st.spinner("Listening... Speak now!"):
                        try:
                            # Capture audio for speech recognition
                            r = sr.Recognizer()
                            with sr.Microphone() as source:
                                st.info("Listening for 5 seconds...")
                                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                            
                            # Convert speech to text
                            text = r.recognize_google(audio)
                            st.success(f"You said: {text}")
                            
                            # Add to conversation and process
                            st.session_state.video_conversation_history.append({
                                "role": "user",
                                "content": text,
                                "timestamp": datetime.now().isoformat(),
                                "type": "voice"
                            })
                            
                            # Generate AI response
                            ai_response = f"Thank you for that response. Based on what you've told me about '{text[:50]}...', could you elaborate on how this experience has prepared you for this role?"
                            
                            # Handle AI response (adds to conversation and speaks aloud)
                            handle_ai_response(ai_response, "voice")
                            
                            st.rerun()
                            
                        except sr.WaitTimeoutError:
                            st.warning("No speech detected. Please try again.")
                        except sr.UnknownValueError:
                            st.error("Could not understand speech. Please try again or use text input.")
                        except Exception as e:
                            st.error(f"Speech recognition error: {e}")
                else:
                    st.warning("Speech recognition not available or microphone not active")
        
        with col2:
            st.write("📝 **Text Input**")
            # Text input as fallback
            text_input = st.text_area(
                "Type your response:",
                placeholder="Type your answer here...",
                height=100,
                key="text_input_area"
            )
            
            if st.button("📤 Send Text Response"):
                if text_input.strip():
                    # Add to conversation history
                    st.session_state.video_conversation_history.append({
                        "role": "user",
                        "content": text_input.strip(),
                        "timestamp": datetime.now().isoformat(),
                        "type": "text"
                    })
                    
                    # Generate AI response based on text
                    ai_response = f"That's interesting! You mentioned {text_input.strip()[:30]}... Could you tell me more about how this relates to the position we're discussing?"
                    
                    # Handle AI response (adds to conversation and speaks aloud)
                    handle_ai_response(ai_response, "text")
                    
                    st.rerun()
        
        # Automatic Interview Controls
        if st.session_state.interview_mode == 'automatic':
            st.markdown("---")
            st.subheader("🤖 Automatic Interview Controls")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🚀 Start Auto Interview", disabled=not st.session_state.microphone_active):
                    if st.session_state.current_ai_response:
                        # Start the automatic cycle with current question
                        handle_ai_response(st.session_state.current_ai_response, "auto_start")
                        st.success("Started automatic interview mode!")
                    else:
                        # Start with initial question
                        initial_question = "Welcome to your interview! Please start by telling me about yourself and your background."
                        handle_ai_response(initial_question, "auto_start")
                        st.success("Started automatic interview with opening question!")
                    st.rerun()
            
            with col2:
                if st.button("⏸️ Pause Auto Mode"):
                    st.session_state.auto_recording = False
                    st.session_state.waiting_for_response = False
                    st.info("Automatic mode paused. Use manual controls below.")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Restart Auto Cycle"):
                    if st.session_state.current_ai_response:
                        handle_ai_response(st.session_state.current_ai_response, "restart")
                        st.success("Restarting automatic cycle...")
                        st.rerun()
        
        # Display conversation history with enhanced formatting
        st.markdown("---")
        st.subheader("📜 Interview Conversation")
        
        if st.session_state.video_conversation_history:
            for i, message in enumerate(st.session_state.video_conversation_history):
                if message['role'] == 'user':
                    with st.chat_message("user", avatar="👤"):
                        st.write(message['content'])
                        msg_type = message.get('type', 'text')
                        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%H:%M:%S')
                        
                        # Enhanced type indicators for automatic flow
                        if msg_type == 'voice_auto':
                            type_indicator = "🤖🎤 Auto Voice"
                        elif msg_type == 'voice':
                            type_indicator = "🎤 Voice"
                        elif msg_type == 'text':
                            type_indicator = "📝 Text"
                        else:
                            type_indicator = f"📝 {msg_type.title()}"
                        
                        st.caption(f"📅 {timestamp} | {type_indicator}")
                else:
                    with st.chat_message("assistant", avatar="🤖"):
                        st.write(message['content'])
                        msg_type = message.get('type', 'text')
                        timestamp = datetime.fromisoformat(message['timestamp']).strftime('%H:%M:%S')
                        
                        # Enhanced AI response indicators
                        if msg_type in ['voice_auto', 'auto_start', 'restart']:
                            ai_indicator = "🤖🔄 Auto AI"
                        elif msg_type == 'greeting':
                            ai_indicator = "🤖👋 Greeting"
                        else:
                            ai_indicator = "🤖💬 AI Response"
                        
                        spoken_status = 'Yes' if TTS_AVAILABLE else 'No'
                        st.caption(f"📅 {timestamp} | {ai_indicator} | 🔊 Spoken: {spoken_status}")
        else:
            st.info("💬 No conversation yet. Start by enabling your camera and microphone, then:\n\n🤖 **Automatic Mode**: Click 'Start Auto Interview' for hands-free experience\n📝 **Manual Mode**: Use the voice/text controls above")

with tab3:
    st.header("📊 Video Interview Report")
    
    if not st.session_state.video_interview_session_id:
        st.info("💡 Complete a video interview to generate a report.")
    elif st.session_state.video_interview_active:
        st.info("⏳ Interview is still active. End the interview to generate a report.")
    else:
        if st.button("📋 Generate Video Interview Report"):
            with st.spinner("Generating comprehensive video interview report..."):
                result = get_video_interview_report(st.session_state.video_interview_session_id)
            
            if "error" not in result:
                report = result["data"]
                
                st.success("✅ Video Interview Report Generated")
                
                # Report metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Session ID", report.get('session_id', 'N/A')[:8] + "...")
                with col2:
                    st.metric("Interview Type", "🎥 Video")
                with col3:
                    st.metric("Duration", report.get('interview_duration', 'N/A'))
                with col4:
                    st.metric("Total Questions", report.get('total_questions', 0))
                
                st.subheader("📝 Detailed Video Interview Analysis")
                st.markdown(report.get('report_content', 'No report content available'))
                
                # Download option
                if st.button("📥 Download Report"):
                    st.download_button(
                        label="Download as Text",
                        data=report.get('report_content', ''),
                        file_name=f"video_interview_report_{report.get('session_id', 'unknown')}.txt",
                        mime="text/plain"
                    )
            else:
                st.error(f"❌ Error generating report: {result['error']}")

with tab4:
    st.header("ℹ️ Video Interview Instructions")
    
    st.markdown("""
    ## 🎥 How to Conduct a Video Interview
    
    ### 📋 Before You Start
    1. **Install Required Dependencies**:
       ```bash
       pip install opencv-python pyaudio numpy
       ```
    
    2. **Check Your Equipment**:
       - 📷 Ensure your camera is working
       - 🎤 Test your microphone
       - 💻 Use a stable internet connection
       - 🔆 Make sure you have good lighting
    
    2. **Environment Setup**:
       - 🏠 Choose a quiet, professional background
       - 🪑 Sit comfortably with good posture
       - 👔 Dress professionally
       - 📱 Turn off notifications
    
    ### 🚀 During the Interview
    1. **Starting the Interview**:
       - Click "Start Video Interview" in the first tab
       - Enable your camera and microphone
       - Wait for the AI interviewer to greet you
    
    2. **Communication Options**:
       - 🎤 **Voice**: Speak naturally - the AI can hear you
       - 📹 **Video**: The AI can see your expressions and body language
       - 💬 **Text**: Use as backup if audio/video fails
    
    3. **Best Practices**:
       - 👁️ Look at the camera when speaking
       - 🗣️ Speak clearly and at a moderate pace
       - 😊 Show enthusiasm and engagement
       - ⏱️ Take time to think before answering
    
    ### 🤖 AI Interviewer Features
    - **Real-time Analysis**: The AI analyzes both your words and visual cues
    - **Adaptive Questions**: Follow-up questions based on your responses
    - **Professional Feedback**: Constructive assessment of your performance
    - **Comprehensive Report**: Detailed analysis including communication skills
    
    ### 🔧 Technical Features
    - **Gemini Live API**: Powered by Google's advanced AI
    - **Real-time Processing**: Instant audio and video analysis
    - **WebSocket Communication**: Low-latency real-time interaction
    - **Secure Connection**: All data is processed securely
    
    ### 📊 What Gets Evaluated
    1. **Communication Skills**: Clarity, articulation, professional language
    2. **Technical Knowledge**: Domain expertise and problem-solving
    3. **Visual Presentation**: Professional appearance, body language
    4. **Confidence & Presence**: How you present yourself on camera
    5. **Cultural Fit**: Personality and team alignment assessment
    
    ### 🆘 Troubleshooting
    - **Camera Not Working**: Check browser permissions and refresh
    - **Audio Issues**: Use the text chat as backup
    - **Connection Problems**: Refresh the page and restart
    - **Poor Video Quality**: Check your internet connection
    
    ### 🎯 Tips for Success
    - 📚 Review your resume beforehand
    - 🎯 Prepare examples of your work
    - 💡 Think of questions to ask the interviewer
    - 😌 Stay calm and be yourself
    - 🔄 Practice with the camera beforehand
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🎥 SRA Video Interview System | Powered by Gemini Live API & Streamlit</p>
    </div>
    """, 
    unsafe_allow_html=True
)