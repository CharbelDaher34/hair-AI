import json
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime

# ---- CONFIGURATION ----
REPORTS_DIR = Path(__file__).parent / "reports"

# ---- PAGE SETUP ----
st.set_page_config(
    page_title="AI Interview Reports", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CUSTOM CSS ----
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin: -1rem -1rem 2rem -1rem;
        padding: 2rem 1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .section-header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
    }
    .question-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        margin: 1rem 0;
    }
    .answer-box {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 0.5rem 0;
    }
    .followup-section {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 1rem 0;
    }
    .evaluation-section {
        background: #d1ecf1;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin: 1rem 0;
    }
    .stats-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ---- HEADER ----
st.markdown("""
<div class="main-header">
    <h1>🤖 AI Interview Reports Dashboard</h1>
    <p>Comprehensive analysis and insights from technical interviews</p>
</div>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
with st.sidebar:
    st.header("📁 Report Selection")
    
    if not REPORTS_DIR.exists():
        st.error(f"Reports directory not found: {REPORTS_DIR}")
        st.stop()

    report_files = sorted(REPORTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not report_files:
        st.warning("No reports found.")
        st.stop()

    # Create more user-friendly display names
    file_options = {}
    for f in report_files:
        # Convert filename back to email format
        email = f.stem.replace('_', '@', 1).replace('_', '.')
        modified_time = datetime.fromtimestamp(f.stat().st_mtime)
        display_name = f"{email} ({modified_time.strftime('%Y-%m-%d %H:%M')})"
        file_options[display_name] = f

    selected_report = st.selectbox(
        "Choose a report:",
        list(file_options.keys()),
        key="report_selectbox"
    )

# Get the selected report path (outside sidebar context)
report_path = file_options[selected_report]

# Show report info in sidebar
with st.sidebar:
    # Report info
    st.markdown("---")
    st.markdown("**📊 Report Info**")
    file_size = report_path.stat().st_size / 1024
    st.write(f"Size: {file_size:.1f} KB")
    st.write(f"Modified: {datetime.fromtimestamp(report_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")

# ---- LOAD DATA ----
def load_report(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

data = load_report(report_path)

# ---- MAIN CONTENT ----
# Summary Section
st.markdown('<h2 class="section-header">📈 Performance Overview</h2>', unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="🎯 Overall Score",
        value=f"{data['overall_score']:.1f}",
        help="Combined technical and communication score"
    )

with col2:
    st.metric(
        label="⚙️ Technical",
        value=f"{data['technical_score']:.1f}",
        help="Technical knowledge and accuracy"
    )

with col3:
    st.metric(
        label="💬 Communication",
        value=f"{data['communication_score']:.1f}",
        help="Clarity and interaction quality"
    )

with col4:
    st.metric(
        label="⏱️ Duration",
        value=data['duration'].split('.')[0],  # Remove microseconds
        help="Total interview time"
    )

with col5:
    st.metric(
        label="❓ Questions",
        value=len(data.get('turns', [])),
        help="Number of questions answered"
    )

# ---- DETAILED ANALYSIS ----
st.markdown('<h2 class="section-header">📝 Question-by-Question Analysis</h2>', unsafe_allow_html=True)

# ---- QUESTION-BY-QUESTION VIEW ----
# (Performance Metrics and Interaction Analysis removed as per request)

# Loop through each question/turn
for idx, (turn, eval_) in enumerate(zip(data['turns'], data['evaluations']), start=1):
    with st.expander(f"Question {idx}: {turn['question'][:80]}{'...' if len(turn['question']) > 80 else ''}"):
        # Question header
        st.markdown(f"**❓ Full Question:** {turn['question']}")
        st.markdown("---")
        
        # Answer section
        col_ans, col_time = st.columns([4, 1])
        with col_ans:
            st.markdown("**💭 Candidate's Answer:**")
            st.write(turn["candidate_answer"])
        
        with col_time:
            st.metric("⏱️ Response Time", f"{turn['response_time_seconds']:.1f}s")
            
            # Interaction metrics
            st.markdown("**📊 Interactions:**")
            st.write(f"📋 Paste: {turn.get('paste_count', 0)}")
            st.write(f"📄 Copy: {turn.get('copy_count', 0)}")
            st.write(f"🗂️ Tab: {turn.get('tab_switch_count', 0)}")
        
        # Follow-up section (if exists)
        if turn.get("followup_question") and turn.get("followup_answer"):
            st.markdown("### 🔄 Follow-up Question")
            st.markdown(f"**Q:** {turn['followup_question']}")
            st.markdown(f"**A:** {turn['followup_answer']}")
            st.caption(f"⏱️ Follow-up response time: {turn.get('followup_response_time_seconds', 0):.1f}s")
        
        # Evaluation section
        tech_score = eval_.get("technical_score", 0)
        comm_score = eval_.get("communication_score", 0)
        overall_local = (tech_score + comm_score) / 2
        
        st.markdown("### 📊 Evaluation Results")
        
        # Score metrics
        score_col1, score_col2, score_col3 = st.columns(3)
        with score_col1:
            st.metric("Technical", f"{tech_score}/100")
            st.progress(tech_score / 100)
        with score_col2:
            st.metric("Communication", f"{comm_score}/100")
            st.progress(comm_score / 100)
        with score_col3:
            st.metric("Combined", f"{overall_local:.1f}/100")
            st.progress(overall_local / 100)
        
        # Feedback
        st.markdown("**💬 Feedback:**")
        st.info(eval_["feedback"])
        
        # Strengths and improvements
        feedback_col1, feedback_col2 = st.columns(2)
        with feedback_col1:
            st.markdown("**✅ Strengths:**")
            for strength in eval_.get("strengths", []):
                st.write(f"• {strength}")
        
        with feedback_col2:
            st.markdown("**📈 Areas for Improvement:**")
            for improvement in eval_.get("improvements", []):
                st.write(f"• {improvement}")
        
        # Ideal answer (collapsible)
        st.markdown("**💡 Ideal Answer:**")
        st.code(turn['ideal_answer'], language="text")

# ---- FOOTER ----
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7f8c8d; padding: 1rem;">
    <p>🤖 AI Interview Reports Dashboard | Generated from: <code>{}</code></p>
</div>
""".format(report_path.name), unsafe_allow_html=True) 