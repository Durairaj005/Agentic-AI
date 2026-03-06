import streamlit as st
import PyPDF2
import re
from datetime import datetime
import hashlib
import tempfile
import os

# Simple page config
st.set_page_config(
    page_title="Bill Fraud Detector",
    page_icon="📄",
    layout="centered"
)

# Simple header
st.title("📄 Bill Fraud Detection System")
st.markdown("Upload a bill/invoice to check if it's **REAL** or **FAKE**")

# Initialize session state
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'result' not in st.session_state:
    st.session_state.result = None

# File upload
uploaded_file = st.file_uploader(
    "Choose a bill/invoice (PDF only)",
    type=['pdf'],
    help="Upload bill or invoice for fraud detection"
)

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name
        
        # Extract text
        text = ""
        with open(tmp_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # Clean up temp file
        os.unlink(tmp_path)
        return text
    except Exception as e:
        return f"Error: {str(e)}"

def detect_fraud(text):
    """Detect fraud indicators in bill text"""
    
    # Initialize results
    fraud_indicators = []
    genuine_indicators = []
    score = 0
    
    # Check for common bill elements (genuine indicators)
    required_elements = [
        (r'invoice|bill|receipt', 'Document type identified'),
        (r'date', 'Date field present'),
        (r'total|amount', 'Total amount field'),
        (r'tax|vat|gst', 'Tax information'),
        (r'[0-9]+\.[0-9]{2}', 'Monetary amounts detected'),
        (r'@|\.com', 'Contact information')
    ]
    
    for pattern, desc in required_elements:
        if re.search(pattern, text.lower()):
            genuine_indicators.append(f"✓ {desc}")
            score += 1
    
    # Check for fraud indicators
    fraud_patterns = [
        (r'free|discount|offer', 'Suspicious promotional language'),
        (r'urgent|immediate payment|due now', 'Pressure tactics'),
        (r'bank account.*(change|updated)', 'Suspicious bank details'),
        (r'paypal|western union|money gram', 'Unusual payment methods'),
        (r'bitcoin|crypto|wire transfer', 'High-risk payment terms'),
        (r'[0-9]{5,}', 'Unusually large numbers'),
        (r'\$\s*[0-9]{4,}', 'Large amount detected'),
        (r'your business is selected', 'Unsolicited business claim'),
        (r'lottery|prize|won', 'Lottery scam indicators'),
        (r'irs|tax authority|government', 'Impersonation attempt')
    ]
    
    for pattern, desc in fraud_patterns:
        if re.search(pattern, text.lower()):
            fraud_indicators.append(f"⚠️ {desc}")
            score -= 2
    
    # Check for missing critical elements
    critical_missing = [
        (r'company|business|llc|inc', 'Company/Business name'),
        (r'address', 'Physical address'),
        (r'phone|tel|fax', 'Phone number'),
        (r'invoice\s*#|number|ref', 'Invoice number')
    ]
    
    for pattern, desc in critical_missing:
        if not re.search(pattern, text.lower()):
            fraud_indicators.append(f"⚠️ Missing: {desc}")
            score -= 1
    
    # Calculate fraud probability
    max_score = len(required_elements) + 4  # 4 critical elements
    min_score = -len(fraud_patterns) - len(critical_missing)
    
    # Normalize to 0-100% fraud probability
    fraud_prob = max(0, min(100, ((max_score - score) / (max_score - min_score)) * 100))
    
    # Determine verdict
    if fraud_prob >= 60:
        verdict = "FAKE"
        verdict_color = "red"
    elif fraud_prob >= 30:
        verdict = "SUSPICIOUS"
        verdict_color = "orange"
    else:
        verdict = "REAL"
        verdict_color = "green"
    
    return {
        'fraud_probability': round(fraud_prob, 1),
        'verdict': verdict,
        'verdict_color': verdict_color,
        'genuine_indicators': genuine_indicators,
        'fraud_indicators': fraud_indicators,
        'score': score
    }

# Analyze button
if uploaded_file is not None:
    if st.button("🔍 Check Bill", type="primary", use_container_width=True):
        with st.spinner("Analyzing bill for fraud indicators..."):
            # Extract text
            text = extract_text_from_pdf(uploaded_file)
            
            if text and not text.startswith("Error"):
                # Analyze
                result = detect_fraud(text)
                st.session_state.result = result
                st.session_state.analysis_done = True
            else:
                st.error("Could not extract text from PDF. Please ensure it's a readable PDF.")
                st.session_state.analysis_done = False

# Display results
if st.session_state.analysis_done and st.session_state.result:
    result = st.session_state.result
    
    st.markdown("---")
    
    # Main verdict - simple and clear
    fraud_prob = result['fraud_probability']
    verdict = result['verdict']
    color = result['verdict_color']
    
    # Big verdict display
    if verdict == "REAL":
        st.success(f"### ✅ VERDICT: REAL BILL")
        st.markdown(f"**Confidence:** {100-fraud_prob:.1f}% genuine")
    elif verdict == "SUSPICIOUS":
        st.warning(f"### ⚠️ VERDICT: SUSPICIOUS")
        st.markdown(f"**Fraud Probability:** {fraud_prob}%")
    else:
        st.error(f"### ❌ VERDICT: FAKE BILL")
        st.markdown(f"**Fraud Probability:** {fraud_prob}%")
    
    # Simple metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Genuine Indicators", len(result['genuine_indicators']))
    with col2:
        st.metric("Fraud Indicators", len(result['fraud_indicators']))
    
    # Two simple columns for indicators
    col1, col2 = st.columns(2)
    
    with col1:
        if result['genuine_indicators']:
            st.markdown("**✅ Genuine Elements Found:**")
            for ind in result['genuine_indicators'][:5]:  # Show top 5
                st.markdown(f"- {ind}")
    
    with col2:
        if result['fraud_indicators']:
            st.markdown("**⚠️ Fraud Indicators Found:**")
            for ind in result['fraud_indicators'][:5]:  # Show top 5
                st.markdown(f"- {ind}")
    
    # Simple recommendation
    st.markdown("---")
    if verdict == "FAKE":
        st.markdown("**🚨 ACTION REQUIRED:** Do NOT pay this bill. Likely fraudulent.")
    elif verdict == "SUSPICIOUS":
        st.markdown("**⚠️ RECOMMENDATION:** Verify with the company before paying.")
    else:
        st.markdown("**✅ RECOMMENDATION:** Bill appears legitimate. Proceed with normal payment process.")
    
    # Reset button
    if st.button("Check Another Bill"):
        st.session_state.analysis_done = False
        st.session_state.result = None
        st.rerun()

else:
    # Simple instructions
    st.markdown("---")
    st.markdown("""
    ### How it works:
    1. Upload a PDF bill/invoice
    2. Click "Check Bill"
    3. Get instant verdict: **REAL**, **SUSPICIOUS**, or **FAKE**
    
    ### What we check:
    - Missing required elements (company name, address, etc.)
    - Suspicious language patterns
    - Unusual payment requests
    - Common scam indicators
    """)

# Simple footer
st.markdown("---")
st.caption("⚠️ This is an AI-assisted screening tool. Always verify suspicious bills through official channels.")