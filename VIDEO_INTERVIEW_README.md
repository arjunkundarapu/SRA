# 🎥 SRA Video Interview System

A real-time AI-powered video interview system using Google Gemini Live API for conducting professional video interviews with audio, video, and text communication.

## 🚀 Features

### Real-time AI Video Interviews
- **Live Audio Processing**: Real-time speech recognition and AI responses
- **Video Analysis**: AI analyzes candidate's visual presentation and body language
- **Text Backup**: Fallback text communication if audio/video fails
- **Adaptive Questioning**: AI generates follow-up questions based on responses
- **Professional Assessment**: Comprehensive evaluation including visual cues

### Technical Capabilities
- **Gemini Live API Integration**: Powered by Google's advanced multimodal AI
- **WebSocket Communication**: Low-latency real-time bidirectional communication
- **Multi-format Support**: Audio (PCM), Video (JPEG frames), and Text
- **Session Management**: Persistent interview sessions with conversation history
- **Database Integration**: All interviews stored in Supabase with full history

## 📋 Prerequisites

### Environment Setup
1. **Google Gemini Live API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Camera & Microphone**: Working webcam and microphone
3. **Python 3.8+**: Latest Python version
4. **Supabase Project**: Configured database (see DATABASE_SCHEMA.md)

### Required Dependencies
```bash
pip install -r requirements.txt
```

New dependencies for video interviews:
- `opencv-python`: Video capture and processing
- `pyaudio`: Audio capture from microphone  
- `numpy`: Array processing for video frames
- `Pillow`: Image processing
- `aiofiles`: Async file operations

## 🛠️ Installation & Setup

### 1. Environment Variables
Update your `.env` file:
```env
# AI Configuration
GEMINI_API_KEY=your_regular_gemini_key
GEMINI_LIVE_API_KEY=your_gemini_live_api_key

# Video Interview Configuration
MAX_VIDEO_DURATION_MINUTES=60
MAX_AUDIO_CHUNK_SIZE=8192
VIDEO_FRAME_RATE=2
```

### 2. Database Schema Updates
Run these SQL commands in your Supabase dashboard:

```sql
-- Add interview_type column to interview_sessions
ALTER TABLE interview_sessions 
ADD COLUMN interview_type TEXT DEFAULT 'text' 
CHECK (interview_type IN ('text', 'video'));

-- Add message_type column to interview_messages  
ALTER TABLE interview_messages 
ADD COLUMN message_type TEXT DEFAULT 'text' 
CHECK (message_type IN ('text', 'audio', 'video'));

-- Add interview_type column to interview_reports
ALTER TABLE interview_reports 
ADD COLUMN interview_type TEXT DEFAULT 'text' 
CHECK (interview_type IN ('text', 'video'));
```

### 3. Start the Services

**Backend (Terminal 1):**
```bash
uvicorn backend.app.main:app --reload
```

**Video Interview Frontend (Terminal 2):**
```bash
streamlit run video_interview_app.py
```

**Regular Streamlit App (Terminal 3, optional):**
```bash
streamlit run streamlit_app.py
```

## 🎯 How to Use

### For Applicants

1. **Start Video Interview**:
   - Navigate to the "Start Video Interview" tab
   - Test your camera and microphone
   - Optionally provide resume data for personalized questions
   - Click "Start Video Interview"

2. **During the Interview**:
   - Enable camera and microphone in the "Live Interview" tab
   - Speak naturally - the AI can hear and see you
   - Use text chat as backup if needed
   - Maintain professional posture and eye contact

3. **End Interview**:
   - Click "End Interview" when finished
   - AI generates comprehensive report including video analysis

### For Recruiters

1. **Monitor Interviews**:
   - Use existing recruiter dashboard
   - View real-time interview statistics
   - Access completed video interview reports

2. **Review Reports**:
   - Video interview reports include visual presentation analysis
   - Comprehensive assessment of both verbal and non-verbal communication
   - Hiring recommendations based on multimodal AI analysis

## 🔧 API Endpoints

### Video Interview Management
```
POST /video-interview/start
POST /video-interview/end/{session_id}
GET  /video-interview/report/{session_id}
```

### WebSocket Communication
```
WS /video-interview/ws/{session_id}
```

### Message Types (WebSocket)
```json
// Audio chunk
{
  "type": "audio_chunk",
  "data": "base64_encoded_audio"
}

// Video frame  
{
  "type": "video_frame",
  "data": "base64_encoded_jpeg"
}

// Text message
{
  "type": "text_message", 
  "content": "Hello, I'm ready for the interview"
}

// End interview
{
  "type": "end_interview"
}
```

## 🎛️ Configuration

### Audio Settings
- **Format**: PCM 16-bit
- **Sample Rate**: 16kHz
- **Channels**: Mono
- **Chunk Size**: 1024 samples

### Video Settings  
- **Format**: JPEG frames
- **Resolution**: 320x240 (resized for bandwidth)
- **Frame Rate**: 2 FPS (configurable)
- **Quality**: 50% JPEG compression

### AI Configuration
- **Model**: gemini-2.0-flash-exp
- **Voice**: Aoede (professional female voice)
- **Response Modalities**: Audio + Text
- **Real-time Processing**: Enabled

## 🔒 Security & Privacy

### Data Handling
- **Local Processing**: Audio/video processed in real-time, not stored permanently
- **Encrypted Communication**: All WebSocket connections secured
- **Database Security**: Only text conversation and metadata stored
- **Privacy Compliance**: No permanent audio/video storage

### Access Control
- **Session-based**: Each interview has unique session ID
- **User Authentication**: Integrated with existing auth system
- **Role-based Access**: Applicants and recruiters have different permissions

## 📊 Performance Considerations

### Bandwidth Requirements
- **Minimum**: 1 Mbps upload for basic functionality
- **Recommended**: 5 Mbps upload for optimal experience
- **Audio**: ~128 kbps
- **Video**: ~500 kbps (at 2 FPS, compressed)

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **CPU**: Multi-core processor for video processing
- **Camera**: 720p or higher resolution
- **Microphone**: Clear audio input device

## 🐛 Troubleshooting

### Common Issues

**Camera Not Working**:
```bash
# Check camera permissions
# On Linux, might need:
sudo usermod -a -G video $USER
```

**Audio Issues**:
```bash
# Install PyAudio dependencies
# Ubuntu/Debian:
sudo apt-get install python3-pyaudio

# macOS:
brew install portaudio
pip install pyaudio

# Windows: Use pre-compiled wheel
pip install pipwin
pipwin install pyaudio
```

**WebSocket Connection Failed**:
- Check if backend is running on port 8000
- Verify Gemini Live API key is valid
- Check internet connection for API access

**Poor Video Quality**:
- Reduce video frame rate in configuration
- Check internet bandwidth
- Ensure good lighting conditions

### Debug Mode
Enable debug logging by setting:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

## 🔄 Architecture Overview

### Components
1. **video_interview_service.py**: Core AI integration and session management
2. **video_interview_router.py**: FastAPI endpoints and WebSocket handling  
3. **video_interview_app.py**: Streamlit frontend for video interviews
4. **Database Schema**: Extended to support video interview metadata

### Data Flow
```
Client Camera/Mic → WebSocket → Gemini Live API → AI Response → Client
                     ↓
                Database (conversation history, reports)
```

### WebSocket Message Flow
```
1. Client connects to /video-interview/ws/{session_id}
2. Session connects to Gemini Live API
3. Client sends audio/video chunks
4. Gemini processes and responds in real-time
5. Server forwards responses to client
6. Conversation saved to database
```

## 🚀 Future Enhancements

### Planned Features
- **Screen Sharing**: Technical interview with code sharing
- **Multi-participant**: Panel interviews with multiple interviewers
- **Recording Options**: Optional session recording (with consent)
- **Advanced Analytics**: Emotion detection, engagement metrics
- **Mobile Support**: React Native app for mobile interviews

### Integration Opportunities
- **Calendar Integration**: Schedule video interviews
- **CRM Integration**: Connect with HR systems
- **Video Conferencing**: Hybrid human-AI interviews
- **Assessment Tools**: Technical coding challenges during video calls

## 📝 Testing

### Manual Testing Checklist
- [ ] Camera initialization works
- [ ] Microphone captures audio
- [ ] WebSocket connection establishes
- [ ] AI responds to audio input
- [ ] AI responds to video input  
- [ ] Text backup communication works
- [ ] Interview can be ended gracefully
- [ ] Report generation includes video analysis
- [ ] Database stores conversation history

### Automated Testing
```bash
# Run backend tests
pytest backend/tests/

# Test video interview endpoints
pytest backend/tests/test_video_interview.py
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/video-improvements`
3. Install dev dependencies: `pip install -r requirements-dev.txt`
4. Make changes and test thoroughly
5. Submit pull request with detailed description

### Code Standards
- Follow existing code style and patterns
- Add comprehensive error handling
- Include docstrings for all functions
- Test both audio and video functionality
- Ensure cross-platform compatibility

## 📄 License

This video interview system is part of the SRA project and follows the same licensing terms.

---

🎥 **Ready to conduct professional AI-powered video interviews!**

For support, please check the troubleshooting section or open an issue in the repository.