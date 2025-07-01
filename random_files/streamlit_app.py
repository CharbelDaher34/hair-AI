import json
from pathlib import Path
import streamlit as st

# ---- CONFIGURATION ----
REPORTS_DIR = Path(__file__).parent / "reports"

st.set_page_config(page_title="AI Interview Reports", page_icon="🤖", layout="wide")
st.title("📄 AI Interview Reports Viewer")

if not REPORTS_DIR.exists():
    st.warning(f"Reports directory not found: {REPORTS_DIR}")
    st.stop()

# Collect json files
report_files = sorted(REPORTS_DIR.glob("*.json"))
if not report_files:
    st.info("No reports found.")
    st.stop()

# Select report
file_display_names = [f.name for f in report_files]
selected = st.selectbox("Select a report file", file_display_names)
report_path = REPORTS_DIR / selected

# Load JSON
with report_path.open("r") as f:
    data = json.load(f)

# ---- SUMMARY METRICS ----
st.subheader("🔍 Overall Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Overall", f"{data['overall_score']:.1f}/100")
col2.metric("Technical", f"{data['technical_score']:.1f}/100")
col3.metric("Communication", f"{data['communication_score']:.1f}/100")
col4.metric("Duration", data['duration'])

st.markdown("---")

# ---- TURN-BY-TURN DETAILS ----
st.subheader("📝 Turn-by-Turn Details")
turns = data.get("turns", [])
evaluations = data.get("evaluations", [])

for idx, (turn, eval_) in enumerate(zip(turns, evaluations), start=1):
    with st.expander(f"Question {idx}: {turn['question'][:60]}..."):
        st.markdown(f"**❓ Question:** {turn['question']}")
        st.markdown(f"**💬 Candidate Answer:** {turn['candidate_answer']}")
        st.caption(f"⏱️ Response time: {turn['response_time_seconds']:.1f}s")
        
        # Follow-up, if any
        if turn.get("followup_question") and turn.get("followup_answer"):
            st.divider()
            st.markdown("**🔄 Follow-up Interaction**")
            st.markdown(f"**Follow-up Q:** {turn['followup_question']}")
            st.markdown(f"**Follow-up A:** {turn['followup_answer']}")
            if turn.get("followup_response_time_seconds") is not None:
                st.caption(
                    f"⏱️ Follow-up response time: {turn['followup_response_time_seconds']:.1f}s"
                )
        
        # Display cumulative counts for entire question
        st.caption(f"📋 Paste events: {turn.get('paste_count', 0)}   |   🗂️ Tab switches: {turn.get('tab_switch_count', 0)} (entire question)")

        st.divider()
        st.markdown("**🧠 Ideal Answer (excerpt):**")
        st.code(turn['ideal_answer'][:400] + ('...' if len(turn['ideal_answer']) > 400 else ''))

        # Evaluation section
        st.markdown("### 📊 Evaluation")
        tech = eval_.get("technical_score", 0)
        comm = eval_.get("communication_score", 0)
        overall_local = (tech + comm) / 2
        pb_cols = st.columns(3)
        with pb_cols[0]:
            st.metric("Technical", f"{tech}")
            st.progress(tech / 100)
        with pb_cols[1]:
            st.metric("Communication", f"{comm}")
            st.progress(comm / 100)
        with pb_cols[2]:
            st.metric("Overall", f"{overall_local:.1f}")
            st.progress(overall_local / 100)

        st.markdown("**Feedback**")
        st.write(eval_["feedback"])

        col_s, col_i = st.columns(2)
        with col_s:
            st.markdown("**Strengths**")
            st.write("\n".join(f"• {s}" for s in eval_.get("strengths", [])))
        with col_i:
            st.markdown("**Improvements**")
            st.write("\n".join(f"• {im}" for im in eval_.get("improvements", [])))

st.markdown("---")
st.caption("© AI Interview Bot") 