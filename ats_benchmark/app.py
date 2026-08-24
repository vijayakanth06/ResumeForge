"""Main Streamlit entrypoint for ATS Resume Benchmark."""
import streamlit as st

# Configure Streamlit page layout
st.set_page_config(
    page_title="ATS Resume Benchmark",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config.settings import settings
from database.db import db
from ui.entry_page import render_entry_page
from ui.dataset_page import render_dataset_page
from ui.analysis_page import render_analysis_page
from ui.paper_figures import render_paper_figures


# Initialize session state for navigation
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "📄 Journal Paper Figures"

# ----------------------------------------------------
# Sidebar Navigation & Progress Tracking
# ----------------------------------------------------
with st.sidebar:
    st.title("📄 ATS Benchmark")
    st.caption("Pure-Manual 50-Report Research Benchmark Suite")
    st.markdown("---")

    # 50-Report Progress Tracker
    all_records = db.get_all_active_comparisons()
    progress_count = len(all_records)
    progress_ratio = min(progress_count / 50.0, 1.0)
    
    st.markdown("##### 📈 Dataset Progress")
    st.progress(progress_ratio)
    st.markdown(f"**{progress_count} / 50** reports recorded (`{int(progress_ratio * 100)}%`)")

    st.markdown("---")
    st.markdown("##### 📊 Quick Overview")
    st.caption(f"• **10 AI Models**: {len(set(r.get('model') for r in all_records))} evaluated")
    st.caption(f"• **5 JDs**: {len(set(r.get('jd') for r in all_records))} evaluated")
    st.caption(f"• **Database**: `{settings.database_path.name}`")

    st.markdown("---")
    st.markdown(
        """
        **System Guarantees:**
        • 🛡️ 100% Deterministic Calculations
        • ⚡ Zero API Calls or Token Limits
        • 🧮 Automatic Advantage & % Increase
        • 📁 Multi-format CSV / JSON / XLSX Export
        • 📄 25+ Publication-Ready Figures
        """
    )


# ----------------------------------------------------
# Main Content Area
# ----------------------------------------------------
st.title("ATS Resume Benchmark & Analysis Suite")

tabs = ["📄 Journal Paper Figures", "🏆 Analytics & Leaderboard", "🗄️ Dataset Explorer & Exports", "📝 Manual Entry"]
active_index = tabs.index(st.session_state["active_tab"]) if st.session_state["active_tab"] in tabs else 0

selected_tab = st.radio(
    "Navigation",
    options=tabs,
    index=active_index,
    horizontal=True,
    label_visibility="collapsed",
)

if selected_tab != st.session_state["active_tab"]:
    st.session_state["active_tab"] = selected_tab

st.markdown("---")

# Render Selected Tab
if st.session_state["active_tab"] == "📄 Journal Paper Figures":
    render_paper_figures()
elif st.session_state["active_tab"] == "🏆 Analytics & Leaderboard":
    render_analysis_page()
elif st.session_state["active_tab"] == "🗄️ Dataset Explorer & Exports":
    render_dataset_page()
elif st.session_state["active_tab"] == "📝 Manual Entry":
    render_entry_page()
