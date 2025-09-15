import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configure Streamlit page
st.set_page_config(
    page_title="SRA Interview System", 
    page_icon="🤖", 
    layout="wide"
)

# API Base URL
API_BASE = "http://127.0.0.1:8000"

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'interview_session_id' not in st.session_state:
    st.session_state.interview_session_id = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'resume_uploaded' not in st.session_state:
    st.session_state.resume_uploaded = False
if 'db_resumes_loaded' not in st.session_state:
    st.session_state.db_resumes_loaded = False
if 'available_resumes' not in st.session_state:
    st.session_state.available_resumes = []
if 'selected_resume_source' not in st.session_state:
    st.session_state.selected_resume_source = None

def register_user(email, password, user_type):
    """Register a new user"""
    try:
        response = requests.post(f"{API_BASE}/auth/register", json={
            "email": email,
            "password": password,
            "user_type": user_type
        })
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Registration failed")}
    except Exception as e:
        return {"error": str(e)}

def login_user(email, password):
    """Login user"""
    try:
        response = requests.post(f"{API_BASE}/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Login failed")}
    except Exception as e:
        return {"error": str(e)}

def upload_resume(applicant_id, file):
    """Upload resume file"""
    try:
        # Prepare the file for upload
        files = {"file": (file.name, file, file.type)}
        data = {"applicant_id": applicant_id}
        
        response = requests.post(f"{API_BASE}/applicant/upload_resume", files=files, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Upload failed") if response.headers.get("content-type", "").startswith("application/json") else response.text
            return {"error": error_detail}
    except Exception as e:
        return {"error": str(e)}

def get_applicant_resumes(applicant_id):
    """Get all resumes for an applicant from database"""
    try:
        response = requests.get(f"{API_BASE}/applicant/resumes/{applicant_id}")
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Failed to fetch resumes") if response.headers.get("content-type", "").startswith("application/json") else response.text
            return {"error": error_detail}
    except Exception as e:
        return {"error": str(e)}

def get_latest_resume_data(applicant_id):
    """Get the most recent resume data for an applicant"""
    try:
        result = get_applicant_resumes(applicant_id)
        if "error" not in result and result.get("resumes"):
            # Get the most recent resume (assuming they're ordered by upload time)
            latest_resume = result["resumes"][0]
            if isinstance(latest_resume, dict):
                return latest_resume.get("parsed_data", {})
        return None
    except Exception as e:
        return None

def start_interview(applicant_id, resume_data=None):
    """Start interview session"""
    try:
        payload = {"applicant_id": applicant_id}
        if resume_data:
            payload["resume_data"] = resume_data
        response = requests.post(f"{API_BASE}/applicant/start_interview", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get("detail", "Failed to start interview") if response.headers.get("content-type", "").startswith("application/json") else response.text
            return {"error": error_detail}
    except Exception as e:
        return {"error": str(e)}

def send_answer(session_id, answer):
    """Send answer and get next question"""
    try:
        payload = {
            "session_id": session_id,
            "answer": answer
        }
        response = requests.post(f"{API_BASE}/api/next_question", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Failed to process answer")}
    except Exception as e:
        return {"error": str(e)}

def finish_interview(session_id):
    """Finish interview and generate report"""
    try:
        response = requests.post(f"{API_BASE}/api/finish_interview", json={"session_id": session_id})
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json().get("detail", "Failed to finish interview")}
    except Exception as e:
        return {"error": str(e)}

# Main App
st.title("🤖 SRA Interview System")
st.markdown("Smart Recruiting Assistant - AI-Powered Interview Platform")

# Sidebar for navigation
st.sidebar.title("Navigation")

if not st.session_state.authenticated:
    # Authentication Section
    auth_option = st.sidebar.selectbox("Choose Action", ["Login", "Register"])
    
    if auth_option == "Register":
        st.header("👤 User Registration")
        
        col1, col2 = st.columns(2)
        with col1:
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
        with col2:
            user_type = st.selectbox("User Type", ["applicant", "recruiter"])
            
        if st.button("Register", type="primary"):
            if reg_email and reg_password:
                result = register_user(reg_email, reg_password, user_type)
                if "error" not in result:
                    st.success(f"✅ Registration successful! User ID: {result.get('user_id')}")
                    st.session_state.user_id = result.get('user_id')
                else:
                    st.error(f"❌ Registration failed: {result['error']}")
            else:
                st.error("Please fill in all fields")
                
    else:  # Login
        st.header("🔐 User Login")
        
        col1, col2 = st.columns(2)
        with col1:
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            
        if st.button("Login", type="primary"):
            if login_email and login_password:
                result = login_user(login_email, login_password)
                if "error" not in result:
                    st.success("✅ Login successful!")
                    st.session_state.authenticated = True
                    user_data = result.get('user', {})
                    st.session_state.user_id = user_data.get('id') if isinstance(user_data, dict) else 'user123'
                    st.session_state.access_token = result.get('access_token')
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {result['error']}")
            else:
                st.error("Please fill in all fields")

else:
    # Authenticated user interface
    st.sidebar.success(f"✅ Logged in as: {st.session_state.user_id}")
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.interview_session_id = None
        st.session_state.conversation_history = []
        st.rerun()
    
    # Main functionality tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Resume Upload", "🎤 Interview", "💬 Chat", "📊 Report"])
    
    with tab1:
        st.header("📄 Resume Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a resume file", 
            type=['pdf', 'docx'],
            help="Upload a PDF or DOCX resume file"
        )
        
        if uploaded_file is not None:
            st.write(f"**File:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size} bytes")
            st.write(f"**Type:** {uploaded_file.type}")
            
            # Show file extension
            file_extension = uploaded_file.name.lower().split('.')[-1] if uploaded_file.name else "unknown"
            st.write(f"**Extension:** .{file_extension}")
            
            if st.button("Upload Resume", type="primary"):
                with st.spinner("Uploading and parsing resume..."):
                    result = upload_resume(st.session_state.user_id, uploaded_file)
                    
                if "error" not in result:
                    st.success("✅ Resume uploaded successfully!")
                    
                    # Display parsed data
                    st.subheader("📋 Parsed Resume Data")
                    parsed_data = result.get('parsed_resume', {})
                    
                    if isinstance(parsed_data, dict):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Contact Info:**")
                            contact_info = parsed_data.get('contact_info', {})
                            st.json(contact_info)
                            
                            st.write("**Skills:**")
                            skills = parsed_data.get('skills', [])
                            if skills and isinstance(skills, list):
                                for skill in skills:
                                    st.badge(skill)
                            else:
                                st.write("No skills detected")
                        
                        with col2:
                            st.write("**Education:**")
                            education = parsed_data.get('education', [])
                            if isinstance(education, list):
                                for edu in education:
                                    st.write(f"• {edu}")
                            
                            st.write("**Experience:**")
                            experience = parsed_data.get('experience', [])
                            if isinstance(experience, list):
                                for exp in experience:
                                    if isinstance(exp, dict):
                                        st.write(f"• {exp.get('period', 'N/A')}: {exp.get('context', 'N/A')}")
                        
                        st.write("**Summary:**")
                        summary = parsed_data.get('summary', 'No summary available')
                        st.info(summary)
                        
                        # Store parsed data in session state for interview
                        st.session_state.resume_data = parsed_data
                    else:
                        st.warning("⚠️ Parsed data format is unexpected")
                    
                else:
                    st.error(f"❌ Upload failed: {result['error']}")
    
    with tab2:
        st.header("🎤 Start Interview")
        
        if st.session_state.interview_session_id is None:
            st.write("Ready to start your AI interview? Click the button below!")
            
            # Check for available resume data
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Resume Data Options")
                
                # Option 1: Use recently uploaded resume data from session
                session_resume_available = 'resume_data' in st.session_state
                use_session_resume = st.checkbox(
                    "Use recently uploaded resume data", 
                    value=session_resume_available,
                    disabled=not session_resume_available
                )
                
                # Option 2: Fetch latest resume from database
                if st.button("🔄 Fetch Latest Resume from Database"):
                    with st.spinner("Fetching resume data..."):
                        db_resume_data = get_latest_resume_data(st.session_state.user_id)
                        if db_resume_data:
                            st.session_state.db_resume_data = db_resume_data
                            st.success("✅ Resume data loaded from database!")
                            st.rerun()
                        else:
                            st.warning("⚠️ No resume found in database. Please upload a resume first.")
                
                db_resume_available = 'db_resume_data' in st.session_state
                use_db_resume = st.checkbox(
                    "Use latest resume from database", 
                    value=db_resume_available,
                    disabled=not db_resume_available
                )
            
            with col2:
                st.subheader("📊 Available Resume Data")
                
                if session_resume_available and use_session_resume:
                    st.info("📄 Using recently uploaded resume data")
                    resume_preview = st.session_state.get('resume_data', {})
                    if isinstance(resume_preview, dict):
                        st.write(f"**Skills:** {', '.join(resume_preview.get('skills', [])[:5])}")
                        st.write(f"**Summary:** {resume_preview.get('summary', 'N/A')[:100]}...")
                
                elif db_resume_available and use_db_resume:
                    st.info("💾 Using database resume data")
                    db_resume_preview = st.session_state.get('db_resume_data', {})
                    if isinstance(db_resume_preview, dict):
                        st.write(f"**Skills:** {', '.join(db_resume_preview.get('skills', [])[:5])}")
                        st.write(f"**Summary:** {db_resume_preview.get('summary', 'N/A')[:100]}...")
                
                else:
                    st.warning("⚠️ No resume data selected")
                    st.info("💡 Upload a resume first or fetch from database")
            
            st.markdown("---")
            
            if st.button("🚀 Start Interview", type="primary"):
                with st.spinner("Starting interview session..."):
                    # Determine which resume data to use
                    resume_data = None
                    if use_session_resume and session_resume_available:
                        resume_data = st.session_state.get('resume_data')
                    elif use_db_resume and db_resume_available:
                        resume_data = st.session_state.get('db_resume_data')
                    
                    result = start_interview(st.session_state.user_id, resume_data)
                    
                if "error" not in result:
                    st.session_state.interview_session_id = result['session_id']
                    st.session_state.conversation_history = [
                        {"role": "assistant", "content": result['message'], "timestamp": datetime.now().isoformat()}
                    ]
                    
                    # Show success message with resume data info
                    resume_info = ""
                    if resume_data:
                        resume_info = " (with resume data)"
                    st.success(f"✅ Interview started{resume_info}! Session ID: {result['session_id']}")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to start interview: {result['error']}")
        else:
            st.success(f"🎤 Interview session active: {st.session_state.interview_session_id}")
            
            if st.button("🔄 Start New Interview"):
                st.session_state.interview_session_id = None
                st.session_state.conversation_history = []
                st.rerun()
    
    with tab3:
        st.header("💬 Interview Chat")
        
        if st.session_state.interview_session_id is None:
            st.warning("⚠️ Please start an interview session first in the Interview tab.")
        else:
            st.info(f"🎤 Active Session: {st.session_state.interview_session_id}")
            
            # Display conversation history
            st.subheader("Conversation History")
            
            for i, message in enumerate(st.session_state.conversation_history):
                if message['role'] == 'assistant':
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(message['content'])
            
            # Input for user response
            user_input = st.text_area(
                "Your Answer:", 
                placeholder="Type your response to the interviewer's question...",
                height=100
            )
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("📤 Send Answer", type="primary", disabled=not user_input.strip()):
                    if user_input.strip():
                        # Add user message to history
                        st.session_state.conversation_history.append({
                            "role": "user", 
                            "content": user_input.strip(), 
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        with st.spinner("AI is thinking..."):
                            result = send_answer(st.session_state.interview_session_id, user_input.strip())
                            
                        if "error" not in result:
                            # Add AI response to history
                            st.session_state.conversation_history.append({
                                "role": "assistant",
                                "content": result['message'],
                                "timestamp": datetime.now().isoformat()
                            })
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to process answer: {result['error']}")
            
            with col2:
                if st.button("🏁 Finish Interview", type="secondary"):
                    with st.spinner("Generating interview report..."):
                        result = finish_interview(st.session_state.interview_session_id)
                        
                    if "error" not in result:
                        st.session_state.interview_report = result
                        st.success("✅ Interview completed! Check the Report tab.")
                    else:
                        st.error(f"❌ Failed to finish interview: {result['error']}")
    
    with tab4:
        st.header("📊 Interview Report")
        
        if 'interview_report' not in st.session_state:
            st.info("💡 Complete an interview to generate a report.")
        else:
            report = st.session_state.interview_report
            
            st.success("✅ Interview Report Generated")
            
            # Report details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Session ID", report.get('session_id', 'N/A'))
            with col2:
                st.metric("Duration", report.get('interview_duration', 'N/A'))
            with col3:
                st.metric("Total Questions", report.get('total_questions', 0))
            
            st.subheader("📝 Detailed Report")
            st.markdown(report.get('report_content', 'No report content available'))
            
            # Option to download report
            if st.button("📥 Download Report"):
                st.download_button(
                    label="Download as Text",
                    data=report.get('report_content', ''),
                    file_name=f"interview_report_{report.get('session_id', 'unknown')}.txt",
                    mime="text/plain"
                )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🤖 SRA Interview System | Built with Streamlit & FastAPI</p>
    </div>
    """, 
    unsafe_allow_html=True
)