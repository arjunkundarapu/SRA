# 🤖 SRA Streamlit Interface

A simple web interface for the Smart Recruiting Assistant (SRA) interview system.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install streamlit
# OR install all requirements
pip install -r requirements.txt
```

### 2. Start the FastAPI Backend
```bash
uvicorn backend.app.main:app --reload
```

### 3. Start the Streamlit App
```bash
streamlit run streamlit_app.py
```

The app will open in your browser at: **http://localhost:8501**

## ✨ Features

### 🔐 Authentication
- **Register**: Create new applicant or recruiter accounts
- **Login**: Authenticate existing users

### 📄 Resume Management
- **Upload**: Upload PDF or DOCX resume files
- **Parse**: Automatically extract skills, experience, education
- **Display**: View parsed resume data in organized format

### 🎤 Interview System
- **Start**: Begin AI-powered interview sessions
- **Chat**: Interactive conversation with AI interviewer
- **Real-time**: Send answers and receive follow-up questions

### 📊 Reports
- **Generate**: Complete interviews to create detailed reports
- **View**: Comprehensive analysis and recommendations
- **Download**: Save reports as text files

## 🎯 How to Use

1. **Register/Login** as an applicant
2. **Upload Resume** (PDF/DOCX) in the Resume Upload tab
3. **Start Interview** using your resume data
4. **Chat** with the AI interviewer in real-time
5. **Finish Interview** to generate a comprehensive report

## 📱 Interface Overview

### Main Tabs
- **📄 Resume Upload**: File upload and parsing
- **🎤 Interview**: Start new interview sessions
- **💬 Chat**: Interactive interview conversation
- **📊 Report**: View generated interview reports

### Features
- ✅ Real-time chat interface
- ✅ Resume parsing and display
- ✅ Session management
- ✅ Report generation and download
- ✅ User authentication
- ✅ Error handling and feedback

## 🔧 API Integration

The Streamlit app integrates with these SRA API endpoints:
- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /applicant/upload_resume` - Resume upload
- `POST /applicant/start_interview` - Start interviews
- `POST /api/next_question` - Send answers
- `POST /api/finish_interview` - Generate reports

## 🛠️ Requirements

- Python 3.8+
- Streamlit
- FastAPI backend running on http://127.0.0.1:8000
- All SRA system dependencies

## 📝 Notes

- Ensure the FastAPI backend is running before starting Streamlit
- Upload resume files in PDF or DOCX format only
- Interview sessions are maintained throughout the browser session
- Reports are generated using AI analysis of the conversation

## 🎉 Ready to Interview!

Your complete SRA interview system is now accessible through a user-friendly web interface!