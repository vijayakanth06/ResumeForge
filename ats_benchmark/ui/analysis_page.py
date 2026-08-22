"""Streamlit UI component: Analytics, Leaderboards, and Category Insights."""
import pandas as pd
import streamlit as st

from analysis.model_summary import generate_model_summary
from analysis.jd_summary import generate_jd_summary
from analysis.category_summary import generate_category_summary
from database.db import db


def render_analysis_page():
    """Renders leaderboards, JD performance, and category breakdowns."""
    st.markdown("### 🏆 AI Resume Model Leaderboard & Analytics")
    st.caption("Comprehensive comparative metrics across the 10 AI models, 5 JDs, and 5 ATS categories.")

    all_records = db.get_all_active_comparisons()
    if not all_records:
        st.info("No comparison records available yet. Enter evaluations in the **Manual Entry** tab to see real-time analytics.")
        return

    # ----------------------------------------------------
    # Model Summary Leaderboard
    # ----------------------------------------------------
    st.markdown("#### 🥇 Model Performance Leaderboard")
    st.caption("Models with all 5 JDs completed receive official rank (1..N). Models with < 5 JDs are marked Provisional.")

    model_data = generate_model_summary(all_records)
    
    leaderboard_rows = []
    for m in model_data:
        rank_display = f"#{m['rank']}" if m.get("rank") is not None else "Provisional"
        adv = m.get("avg_advantage")
        adv_str = f"+{adv:.2f}" if adv is not None and adv > 0 else (f"{adv:.2f}" if adv is not None else "-")
        rel_inc = m.get("avg_relative_increase")
        rel_str = f"{rel_inc:+.1f}%" if rel_inc is not None else "-"
        
        leaderboard_rows.append({
            "Rank": rank_display,
            "AI Model": m["model"],
            "Evaluated JDs": f"{m['jd_count']} / 5",
            "Avg ATS Advantage": adv_str,
            "Relative Increase": rel_str,
            "Win Rate": f"{m['win_rate_percent']}% ({m['ai_wins']}W-{m['human_wins']}L-{m['ties']}T)",
            "Avg AI Score": m.get("avg_ai_overall") or "-",
            "Avg Human Score": m.get("avg_human_overall") or "-",
            "Keyword (25%)": m.get("avg_keyword_match") or "-",
            "Skills (25%)": m.get("avg_skills_coverage") or "-",
            "Formatting (15%)": m.get("avg_ats_formatting") or "-",
            "Role Fit (20%)": m.get("avg_role_alignment") or "-",
            "Impact (15%)": m.get("avg_impact_metrics") or "-",
        })

    df_leaderboard = pd.DataFrame(leaderboard_rows)
    st.dataframe(df_leaderboard, width="stretch", hide_index=True)

    # ----------------------------------------------------
    # Visual Chart: Average Advantage by Model
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("#### 📊 Average ATS Advantage by AI Model")
    
    chart_data = []
    for m in model_data:
        if m.get("avg_advantage") is not None:
            chart_data.append({
                "Model": m["model"],
                "Average Advantage (Points)": m["avg_advantage"],
            })
    
    if chart_data:
        df_chart = pd.DataFrame(chart_data).set_index("Model")
        st.bar_chart(df_chart, width="stretch")

    # ----------------------------------------------------
    # JD Level Breakdown
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("#### 📋 Performance by Job Description (JD1 – JD5)")
    jd_data = generate_jd_summary(all_records)
    
    jd_rows = []
    for j in jd_data:
        adv = j.get("avg_advantage")
        adv_str = f"+{adv:.2f}" if adv is not None and adv > 0 else (f"{adv:.2f}" if adv is not None else "-")
        jd_rows.append({
            "Job Description": j["jd"],
            "Models Evaluated": f"{j['model_count']} / 10",
            "Avg AI Score": j.get("avg_ai_score") or "-",
            "Avg Human Score": j.get("avg_human_score") or "-",
            "Avg Advantage": adv_str,
            "AI Win Rate": f"{j['ai_win_rate_percent']}% ({j['ai_wins']}W-{j['human_wins']}L-{j['ties']}T)",
        })
    df_jd = pd.DataFrame(jd_rows)
    st.dataframe(df_jd, width="stretch", hide_index=True)

    # ----------------------------------------------------
    # Category Level Breakdown
    # ----------------------------------------------------
    st.markdown("---")
    st.markdown("#### 🎯 Category Breakdown (AI vs Human)")
    cat_data = generate_category_summary(all_records)

    cat_rows = []
    for c in cat_data:
        adv = c.get("avg_advantage")
        adv_str = f"+{adv:.2f}" if adv is not None and adv > 0 else (f"{adv:.2f}" if adv is not None else "-")
        cat_rows.append({
            "Category": c["category"],
            "Weight": f"{int(c['weight']*100)}%",
            "Avg AI Score": c.get("avg_ai_score") or "-",
            "Avg Human Score": c.get("avg_human_score") or "-",
            "Avg Advantage": adv_str,
            "AI Wins": c["ai_wins"],
            "Human Wins": c["human_wins"],
            "Ties": c["ties"],
        })
    df_cat = pd.DataFrame(cat_rows)
    st.dataframe(df_cat, width="stretch", hide_index=True)
