"""
Extension Request Sorter - Modern Streamlit Web UI
==================================================
A modern, dark-navy themed dashboard for triaging university extension requests.
Reuses existing backend functions from main.py without altering policy or extraction logic.
"""

import os
import io
import csv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import core backend functions directly from main.py
from main import (
    load_courses,
    load_system_prompt,
    load_env_file,
    classify,
    is_valid,
    recommend,
    sanitize_summary,
    write_reports,
    CATEGORY_WITHIN_POLICY,
    CATEGORY_NEEDS_FACULTY_REVIEW,
    CATEGORY_NEEDS_MORE_INFO,
    MAX_AUTO_DAYS,
    ALLOWED_AUTO_REASONS
)

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Extension Request Sorter | Academic AI Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CUSTOM CSS: MODERN DARK NAVY & BLUE THEME
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global Background and Colors */
    .stApp {
        background-color: #0d131f;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111a2e;
        border-right: 1px solid #1e293b;
    }
    
    /* Top Header Bar */
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px 24px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .main-title {
        color: #f8fafc;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 4px;
    }
    
    /* Modern Stat Cards */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    .metric-card {
        background-color: #151f33;
        border: 1px solid #24324f;
        border-radius: 10px;
        padding: 16px 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    }
    .metric-title {
        font-size: 0.82rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    .metric-badge {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
    }
    
    /* Badge color variants */
    .badge-blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .badge-green { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .badge-purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }

    /* Faculty Notice Box */
    .faculty-callout {
        background: #172554;
        border-left: 4px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin-bottom: 20px;
        color: #bfdbfe;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS & DATA ACCESS
# -----------------------------------------------------------------------------
@st.cache_data
def get_catalog():
    """Load valid courses from courses.csv."""
    return load_courses("courses.csv")

def get_results_df():
    """Load current results.csv into pandas DataFrame."""
    if os.path.exists("results.csv"):
        return pd.read_csv("results.csv")
    return pd.DataFrame()

def get_review_queue_df():
    """Load current review_queue.csv into pandas DataFrame."""
    if os.path.exists("review_queue.csv"):
        return pd.read_csv("review_queue.csv")
    return pd.DataFrame()

def get_summary_text():
    """Read summary.txt report."""
    if os.path.exists("summary.txt"):
        with open("summary.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "Summary report not yet generated. Run the pipeline first."

def run_backend_processing(requests_data_list):
    """
    Executes backend pipeline using existing main.py functions.
    Does not duplicate or change policy logic.
    """
    load_env_file()
    system_prompt = load_system_prompt()
    courses = load_courses("courses.csv")
    
    processed = []
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    
    total = len(requests_data_list)
    for idx, req in enumerate(requests_data_list):
        req_id = req["request_id"]
        raw_text = req["request_text"]
        
        status_text.text(f"Processing request {idx + 1} of {total}: {req_id}...")
        
        # 1. LLM Extraction (or fallback)
        extracted = classify(raw_text, system_prompt)
        
        # 2. Privacy sanitization
        cleaned_summary = sanitize_summary(
            extracted.get("summary", ""),
            extracted.get("reason", "other"),
            extracted.get("course")
        )
        extracted["summary"] = cleaned_summary
        
        # 3. Python Validation
        valid, issues = is_valid(extracted, raw_text, courses)
        
        # 4. Recommendation Engine
        rec, policy_notes = recommend(extracted, issues)
        
        processed.append({
            "request_id": req_id,
            "student_id": req["student_id"],
            "original_request_text": raw_text,
            "course": extracted.get("course"),
            "days": extracted.get("days"),
            "reason": extracted.get("reason"),
            "summary": extracted.get("summary"),
            "recommendation": rec,
            "policy_notes": policy_notes,
            "validation_issues": issues
        })
        progress_bar.progress((idx + 1) / total)
        
    status_text.text("Generating reports (results.csv, review_queue.csv, summary.txt)...")
    write_reports(processed)
    progress_bar.empty()
    status_text.empty()
    return processed

# -----------------------------------------------------------------------------
# SIDEBAR NAVIGATION & SYSTEM BADGE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom: 15px;">
            <div style="background:#2563eb; width:38px; height:38px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:20px;">🎓</div>
            <div>
                <div style="font-weight:700; font-size:1.05rem; color:#f8fafc;">Academic Sorter</div>
                <div style="font-size:0.75rem; color:#94a3b8;">AI Capstone Project</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio(
        "Navigation",
        ["Dashboard", "Submit / Upload Requests", "All Requests", "Faculty Review", "Reports"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### ⚙️ System Policy Bounds")
    st.markdown(f"""
    - **Max Standard Days:** `{MAX_AUTO_DAYS} days`
    - **Auto Reasons:** `{', '.join(ALLOWED_AUTO_REASONS)}`
    - **Decision Authority:** Faculty Only
    - **Privacy Filter:** PII / Illness Redaction Active
    """)
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size:0.75rem; color:#64748b; text-align:center;">
        Extension Request Sorter v1.0<br>
        First-Year AI Capstone Project
    </div>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MAIN APP HEADER
# -----------------------------------------------------------------------------
st.markdown(f"""
    <div class="main-header">
        <div>
            <h1 class="main-title">Extension Request Sorter</h1>
            <div class="sub-title">Intelligent intake, policy sorting, and human-in-the-loop triage for university faculty</div>
        </div>
        <div>
            <span class="metric-badge badge-blue">● Policy Engine Active</span>
        </div>
    </div>
""", unsafe_allow_html=True)

results_df = get_results_df()
review_df = get_review_queue_df()

# =============================================================================
# PAGE 1: DASHBOARD
# =============================================================================
if menu == "Dashboard":
    st.subheader("📊 Executive Overview & Real-Time Metrics")
    
    if results_df.empty:
        st.info("No requests currently processed. Go to **Submit / Upload Requests** to run the intake pipeline.")
    else:
        # Calculate dynamic counts from actual data
        total_requests = len(results_df)
        within_policy_cnt = len(results_df[results_df["recommendation"] == CATEGORY_WITHIN_POLICY])
        faculty_review_cnt = len(results_df[results_df["recommendation"] == CATEGORY_NEEDS_FACULTY_REVIEW])
        more_info_cnt = len(results_df[results_df["recommendation"] == CATEGORY_NEEDS_MORE_INFO])
        
        # Display 4 Stat Cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Total Requests</div>
                    <div class="metric-value">{total_requests}</div>
                    <span class="metric-badge badge-blue">100% Ingested</span>
                </div>
            """, unsafe_allow_html=True)
            
        with col2:
            pct_wp = (within_policy_cnt / total_requests * 100) if total_requests else 0
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Within Policy</div>
                    <div class="metric-value" style="color: #4ade80;">{within_policy_cnt}</div>
                    <span class="metric-badge badge-green">{pct_wp:.1f}% Standard</span>
                </div>
            """, unsafe_allow_html=True)
            
        with col3:
            pct_fr = (faculty_review_cnt / total_requests * 100) if total_requests else 0
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Needs Faculty Review</div>
                    <div class="metric-value" style="color: #fbbf24;">{faculty_review_cnt}</div>
                    <span class="metric-badge badge-amber">{pct_fr:.1f}% Discretionary</span>
                </div>
            """, unsafe_allow_html=True)
            
        with col4:
            pct_mi = (more_info_cnt / total_requests * 100) if total_requests else 0
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Needs More Info</div>
                    <div class="metric-value" style="color: #c084fc;">{more_info_cnt}</div>
                    <span class="metric-badge badge-purple">{pct_mi:.1f}% Incomplete</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Plotly Visualizations (Interactive & Modern)
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### Recommendation Distribution")
            rec_counts = results_df["recommendation"].value_counts().reset_index()
            rec_counts.columns = ["Recommendation", "Count"]
            
            # Professional color mapping
            color_map = {
                CATEGORY_WITHIN_POLICY: "#22c55e",
                CATEGORY_NEEDS_FACULTY_REVIEW: "#f59e0b",
                CATEGORY_NEEDS_MORE_INFO: "#a855f7"
            }
            
            fig_pie = px.pie(
                rec_counts,
                names="Recommendation",
                values="Count",
                color="Recommendation",
                color_discrete_map=color_map,
                hole=0.45
            )
            fig_pie.update_layout(
                paper_bgcolor="#111a2e",
                plot_bgcolor="#111a2e",
                font_color="#e2e8f0",
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(t=20, b=20, l=20, r=20),
                height=340
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with chart_col2:
            st.markdown("#### Requests by Course")
            course_counts = results_df["course"].fillna("Missing").value_counts().reset_index()
            course_counts.columns = ["Course", "Count"]
            
            fig_bar = px.bar(
                course_counts,
                x="Course",
                y="Count",
                color="Count",
                color_continuous_scale="Blues",
                text="Count"
            )
            fig_bar.update_layout(
                paper_bgcolor="#111a2e",
                plot_bgcolor="#111a2e",
                font_color="#e2e8f0",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#1e293b"),
                coloraxis_showscale=False,
                margin=dict(t=20, b=20, l=20, r=20),
                height=340
            )
            fig_bar.update_traces(textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        # Recent Triage Stream
        st.markdown("#### 🕒 Latest Processed Requests (Summary View)")
        recent_preview = results_df[["request_id", "student_id", "course", "days", "reason", "recommendation"]].head(6)
        st.dataframe(recent_preview, use_container_width=True, hide_index=True)

# =============================================================================
# PAGE 2: SUBMIT / UPLOAD REQUESTS
# =============================================================================
elif menu == "Submit / Upload Requests":
    st.subheader("📥 Submit or Upload Extension Requests")
    st.markdown("Upload a new `requests.csv` or process the default dataset through the AI extraction and policy pipeline.")
    
    tab1, tab2 = st.tabs(["📁 Batch CSV Upload", "✍️ Single Request Intake"])
    
    with tab1:
        uploaded_file = st.file_uploader("Upload Student Requests CSV", type=["csv"])
        
        target_records = []
        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                st.success(f"Uploaded file loaded: {len(df_upload)} requests found.")
                st.markdown("**Preview of Uploaded Data:**")
                st.dataframe(df_upload.head(5), use_container_width=True, hide_index=True)
                
                # Convert to dict format
                for _, row in df_upload.iterrows():
                    target_records.append({
                        "request_id": str(row.get("request_id", "")),
                        "student_id": str(row.get("student_id", "")),
                        "request_text": str(row.get("request_text", ""))
                    })
            except Exception as e:
                st.error(f"Error reading CSV: {e}")
        else:
            st.info("Using default `requests.csv` from the project repository.")
            if os.path.exists("requests.csv"):
                default_df = pd.read_csv("requests.csv")
                st.markdown(f"**Previewing Default `requests.csv` ({len(default_df)} requests):**")
                st.dataframe(default_df.head(5), use_container_width=True, hide_index=True)
                
                for _, row in default_df.iterrows():
                    target_records.append({
                        "request_id": str(row.get("request_id", "")),
                        "student_id": str(row.get("student_id", "")),
                        "request_text": str(row.get("request_text", ""))
                    })

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Process Requests with Python Policy Engine", type="primary"):
            if not target_records:
                st.warning("No valid records found to process.")
            else:
                with st.spinner("Executing extraction and triage pipeline..."):
                    results = run_backend_processing(target_records)
                    st.success(f"Successfully triaged {len(results)} requests! Generated results.csv, review_queue.csv, and summary.txt.")
                    st.rerun()

    with tab2:
        st.markdown("Test single student request extraction and immediate policy categorization:")
        test_id = st.text_input("Request ID", value="REQ-TEST-01")
        test_student = st.text_input("Student ID", value="STU9999")
        test_text = st.text_area(
            "Student Request Text",
            value="Dear Dr. Alan, I had severe acute viral fever and need 2 days extension for CS101 assignment."
        )
        
        if st.button("Evaluate Single Request", type="secondary"):
            single_record = [{
                "request_id": test_id,
                "student_id": test_student,
                "request_text": test_text
            }]
            with st.spinner("Extracting with LLM and applying policy..."):
                run_backend_processing(single_record)
                st.success("Request processed! View the output in All Requests or Faculty Review.")
                st.rerun()

# =============================================================================
# PAGE 3: ALL REQUESTS
# =============================================================================
elif menu == "All Requests":
    st.subheader("📋 All Processed Requests")
    st.markdown("Audited list of requests with extracted metadata and policy recommendations. *(Student-safe view: raw emails redacted)*")
    
    if results_df.empty:
        st.warning("No results available. Please process requests first.")
    else:
        # Search and Filters
        filter_col1, filter_col2, filter_col3 = st.columns([2, 1, 1])
        with filter_col1:
            search_query = st.text_input("🔍 Search by Student ID, Request ID, or Course Code", "")
        with filter_col2:
            selected_rec = st.selectbox(
                "Filter by Recommendation",
                ["All", CATEGORY_WITHIN_POLICY, CATEGORY_NEEDS_FACULTY_REVIEW, CATEGORY_NEEDS_MORE_INFO]
            )
        with filter_col3:
            all_reasons = ["All"] + sorted(results_df["reason"].dropna().unique().tolist())
            selected_reason = st.selectbox("Filter by Reason", all_reasons)

        filtered_df = results_df.copy()

        # Apply Filters
        if search_query:
            q = search_query.lower()
            filtered_df = filtered_df[
                filtered_df["request_id"].astype(str).str.lower().str.contains(q) |
                filtered_df["student_id"].astype(str).str.lower().str.contains(q) |
                filtered_df["course"].astype(str).str.lower().str.contains(q)
            ]
            
        if selected_rec != "All":
            filtered_df = filtered_df[filtered_df["recommendation"] == selected_rec]
            
        if selected_reason != "All":
            filtered_df = filtered_df[filtered_df["reason"] == selected_reason]

        st.markdown(f"**Showing {len(filtered_df)} of {len(results_df)} total records:**")

        # Color-coded display table
        def style_rec(val):
            if val == CATEGORY_WITHIN_POLICY:
                return 'background-color: rgba(34, 197, 94, 0.2); color: #86efac; font-weight: bold;'
            elif val == CATEGORY_NEEDS_FACULTY_REVIEW:
                return 'background-color: rgba(245, 158, 11, 0.2); color: #fde047; font-weight: bold;'
            elif val == CATEGORY_NEEDS_MORE_INFO:
                return 'background-color: rgba(168, 85, 247, 0.2); color: #d8b4fe; font-weight: bold;'
            return ''

        display_cols = ["request_id", "student_id", "course", "days", "reason", "summary", "recommendation", "policy_notes"]
        styled_df = filtered_df[display_cols].style.map(style_rec, subset=['recommendation'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# =============================================================================
# PAGE 4: FACULTY REVIEW
# =============================================================================
elif menu == "Faculty Review":
    st.subheader("👨‍🏫 Faculty Review Queue")
    
    st.markdown("""
        <div class="faculty-callout">
            <strong>🔒 Human Authority & Privacy Notice:</strong><br>
            Original student request texts are strictly displayed only on this faculty interface.
            The AI and Python systems <strong>never</strong> make automated approval or rejection decisions. 
            Final authority rests entirely with course instructors.
        </div>
    """, unsafe_allow_html=True)
    
    if review_df.empty:
        st.success("🎉 The faculty review queue is empty! All current requests were resolved or are within policy.")
    else:
        st.markdown(f"**{len(review_df)} Requests Awaiting Human Faculty Review:**")
        
        # Interactive Card/Table View
        for idx, row in review_df.iterrows():
            with st.expander(f"⚠️ {row['request_id']} | Student: {row['student_id']} | Course: {row['course']} | Status: {row['recommendation'].upper()}"):
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    st.markdown(f"**Course:** `{row['course']}`")
                    st.markdown(f"**Days Requested:** `{row['days']}`")
                with c2:
                    st.markdown(f"**Reason Category:** `{row['reason']}`")
                    st.markdown(f"**System Flag:** `{row['recommendation']}`")
                with c3:
                    st.markdown(f"**Policy Flag Reason:** *{row['policy_notes']}*")
                
                st.markdown("---")
                st.markdown("**Original Student Email / Request Text (Faculty Confidential):**")
                st.info(f"\"{row['original_request_text']}\"")
                
                # Human Decision Action Buttons
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 2])
                with btn_col1:
                    if st.button(f"Approve", key=f"app_{row['request_id']}"):
                        st.success(f"Request {row['request_id']} approved by faculty.")
                with btn_col2:
                    if st.button(f"Reject", key=f"rej_{row['request_id']}"):
                        st.error(f"Request {row['request_id']} rejected by faculty.")
                with btn_col3:
                    if st.button(f"Request Proof", key=f"prf_{row['request_id']}"):
                        st.warning(f"Sent documentation request to {row['student_id']}.")

# =============================================================================
# PAGE 5: REPORTS
# =============================================================================
elif menu == "Reports":
    st.subheader("📑 Analytical Reports & Data Export")
    st.markdown("Audit trails, aggregation reports, and CSV download artifacts for university compliance.")
    
    rep_col1, rep_col2 = st.columns([3, 2])
    
    with rep_col1:
        st.markdown("#### Official Summary Report (`summary.txt`)")
        sum_text = get_summary_text()
        st.code(sum_text, language="text")
        
    with rep_col2:
        st.markdown("#### 💾 Artifact Downloads")
        st.markdown("Export processed records and logs directly for university recordkeeping:")
        
        # Download results.csv
        if os.path.exists("results.csv"):
            with open("results.csv", "rb") as f:
                st.download_button(
                    label="📥 Download results.csv (Student-Safe)",
                    data=f,
                    file_name="results.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        # Download review_queue.csv
        if os.path.exists("review_queue.csv"):
            with open("review_queue.csv", "rb") as f:
                st.download_button(
                    label="📥 Download review_queue.csv (Faculty Only)",
                    data=f,
                    file_name="review_queue.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        # Download summary.txt
        if os.path.exists("summary.txt"):
            with open("summary.txt", "rb") as f:
                st.download_button(
                    label="📥 Download summary.txt (Aggregated Report)",
                    data=f,
                    file_name="summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
        st.markdown("---")
        st.markdown("#### 📘 Capstone Documentation")
        docs = [
            ("Project Specification", "docs_project_specification.md"),
            ("Judgment Framework", "docs_judgment_framework.md"),
            ("Cost & Latency Report", "docs_cost_latency_report.md"),
            ("AI Decision Journal", "docs_ai_decision_journal.md"),
            ("Student Reflection Essay", "docs_reflection.md"),
        ]
        for name, doc_path in docs:
            if os.path.exists(doc_path):
                with open(doc_path, "r", encoding="utf-8") as df:
                    doc_content = df.read()
                st.download_button(
                    label=f"📄 Download {name}",
                    data=doc_content,
                    file_name=doc_path,
                    mime="text/markdown",
                    use_container_width=True
                )
