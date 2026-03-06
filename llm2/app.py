import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyPDFLoader
import tempfile

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
    }
    .analysis-result {
        padding: 2rem;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🧠 AI Resume Analyzer</h1><p>Upload your resume and get professional AI-powered analysis for your target job role</p></div>', unsafe_allow_html=True)

# Sidebar for instructions
with st.sidebar:
    st.header("📋 How to Use")
    st.markdown("""
    1. **Upload Resume** - Upload your PDF resume
    2. **Enter Job Role** - Type the position you're targeting
    3. **Get Analysis** - AI will analyze your resume
    4. **Review Results** - See match score and suggestions
    
    ### 📊 What You'll Get:
    - Skills detected
    - Match percentage
    - Missing skills
    - Improvement tips
    - ATS score
    """)
    
    st.header("🔑 API Key Status")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        st.success("✅ API Key is configured")
    else:
        st.error("❌ API Key not found. Please check your .env file")

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.header("📤 Upload Resume")
    uploaded_file = st.file_uploader(
        "Choose your resume (PDF format)", 
        type="pdf",
        help="Upload your resume in PDF format for analysis"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        st.info(f"📄 File size: {uploaded_file.size/1024:.2f} KB")

with col2:
    st.header("🎯 Target Job Role")
    job_role = st.text_input(
        "Enter the job role you're targeting",
        placeholder="e.g., Data Scientist, Software Engineer, Marketing Manager",
        help="Be specific for better analysis"
    )
    
    # Quick job suggestions
    st.markdown("**Quick suggestions:**")
    job_suggestions = ["Data Scientist", "Software Engineer", "Product Manager", "Marketing Manager", "UX Designer"]
    selected_suggestion = st.selectbox("Or choose from popular roles:", [""] + job_suggestions)
    if selected_suggestion and not job_role:
        job_role = selected_suggestion
        st.rerun()

# Analyze button
if uploaded_file and job_role:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.button("🔍 Analyze Resume", use_container_width=True)
    
    if analyze_button:
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name
            
            # Load and extract text from PDF
            with st.spinner("📖 Reading resume..."):
                loader = PyPDFLoader(temp_path)
                documents = loader.load()
                
                resume_text = ""
                for doc in documents:
                    resume_text += doc.page_content + "\n"
                
                st.success("✅ Resume text extracted successfully")
            
            # Initialize LLM
            with st.spinner("🤖 AI is analyzing your resume..."):
                llm = ChatOpenAI(
                    model="openai/gpt-4o-mini",
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENAI_API_KEY"),
                    temperature=0.7,
                    max_tokens=2000
                )
                
                # Create prompt
                prompt = f"""You are an expert HR recruiter and resume reviewer with 15+ years of experience.

                Analyze this resume for the job role: {job_role}

                RESUME CONTENT:
                {resume_text}

                Please provide a comprehensive analysis in the following format:

                📊 **OVERALL MATCH**
                - Match Percentage: [0-100%]
                - ATS Score: [0-100]

                🛠️ **SKILLS DETECTED**
                - Technical Skills: [List skills found]
                - Soft Skills: [List skills found]
                - Relevant Experience: [Brief summary]

                ❌ **MISSING SKILLS**
                - Critical Missing Skills: [Must-have skills not found]
                - Nice-to-have Missing Skills: [Optional skills not found]

                💡 **KEY IMPROVEMENTS**
                - [Specific, actionable suggestions for improvement]
                - [Focus on skills to add or highlight]
                - [Formatting or content suggestions]

                📈 **CAREER PROGRESSION**
                - [Analysis of career growth shown in resume]
                - [Strengths in career trajectory]

                ⚡ **QUICK TIPS**
                - [3-5 immediate actions to improve resume]

                Make your analysis specific, actionable, and tailored to the {job_role} position. Use bullet points for clarity.
                """
                
                # Get analysis
                response = llm.invoke(prompt)
                
            # Display results
            st.markdown("---")
            st.markdown('<div class="analysis-result">', unsafe_allow_html=True)
            
            # Create columns for key metrics
            col1, col2, col3 = st.columns(3)
            
            # Try to extract match percentage from response
            import re
            match_pattern = r'Match Percentage:?\s*(\d+)%?'
            match_search = re.search(match_pattern, response.content)
            
            ats_pattern = r'ATS Score:?\s*(\d+)%?'
            ats_search = re.search(ats_pattern, response.content)
            
            with col1:
                if match_search:
                    match_percent = match_search.group(1)
                    st.metric("🎯 Match Score", f"{match_percent}%")
                else:
                    st.metric("🎯 Match Score", "N/A")
            
            with col2:
                if ats_search:
                    ats_score = ats_search.group(1)
                    st.metric("📊 ATS Score", f"{ats_score}%")
                else:
                    st.metric("📊 ATS Score", "N/A")
            
            with col3:
                st.metric("📄 Resume Length", f"{len(resume_text.split())} words")
            
            st.markdown("---")
            
            # Full analysis
            st.subheader("📋 Detailed Analysis")
            st.markdown(response.content)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Download button for analysis
            analysis_text = f"AI Resume Analysis for {job_role}\n\n{response.content}"
            st.download_button(
                label="📥 Download Analysis",
                data=analysis_text,
                file_name=f"resume_analysis_{job_role.replace(' ', '_')}.txt",
                mime="text/plain"
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("Please check your API key and try again")
            
elif uploaded_file and not job_role:
    st.warning("⚠️ Please enter a target job role")
elif not uploaded_file and job_role:
    st.warning("⚠️ Please upload a resume")
else:
    st.info("👆 Start by uploading your resume and entering a job role")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 1rem;'>
        <p>Made with ❤️ using Streamlit and AI | For educational purposes</p>
        <p style='font-size: 0.8rem;'>Your data is processed temporarily and not stored</p>
    </div>
    """,
    unsafe_allow_html=True
)