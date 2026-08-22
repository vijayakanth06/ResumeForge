"""Streamlit UI component: Side-by-Side Manual Data Entry Page."""
import streamlit as st
from config.settings import CONTROLLED_MODELS, CONTROLLED_JDS
from database.db import db
from database.models import ComparisonRecord
from calculation.engine import (
    calculate_weighted_score,
    calculate_advantage,
    calculate_relative_increase,
    determine_winner,
    check_math_consistency,
)
from calculation.validators import validate_manual_entry


def render_entry_page():
    """Renders the side-by-side manual score entry and live calculation form."""
    st.markdown("### 📝 New ATS Comparison Input")
    st.caption("Enter the Claude ATS analysis scores directly. Advantages and weighted sums are calculated deterministically in real-time.")

    # ----------------------------------------------------
    # Top Metadata Row
    # ----------------------------------------------------
    col_id, col_model, col_jd = st.columns([1.5, 2.5, 1.5])
    
    # Auto-increment default comparison ID
    suggested_id = db.get_next_comparison_id()
    
    with col_id:
        comparison_id = st.text_input(
            "Comparison ID",
            value=st.session_state.get("entry_comp_id", suggested_id),
            help="Unique ID for this comparison run (e.g. C001, C002, ...)",
        )
    with col_model:
        selected_model = st.selectbox(
            "AI Resume Model",
            options=CONTROLLED_MODELS,
            index=CONTROLLED_MODELS.index(st.session_state.get("entry_model", CONTROLLED_MODELS[0])),
            help="Select the exact AI model evaluated in the report.",
        )
    with col_jd:
        selected_jd = st.selectbox(
            "Job Description (JD)",
            options=CONTROLLED_JDS,
            index=CONTROLLED_JDS.index(st.session_state.get("entry_jd", CONTROLLED_JDS[0])),
            help="Select the JD evaluated.",
        )

    # Claude Chat URL
    claude_url = st.text_input(
        "Claude Chat URL (Traceability Metadata)",
        value=st.session_state.get("entry_url", ""),
        placeholder="https://claude.ai/share/...",
        help="Optional URL of the Claude analysis chat.",
    )

    st.markdown("---")

    # ----------------------------------------------------
    # Side-by-Side Dual-Card Score Input
    # ----------------------------------------------------
    col_ai, col_mid, col_human = st.columns([1.2, 0.8, 1.2])

    # Left Column: AI Resume Scores
    with col_ai:
        st.markdown(f"#### 🤖 AI Resume: `{selected_model}`")
        ai_status = st.selectbox(
            "AI Status",
            options=["STRONG MATCH", "MODERATE MATCH", "WEAK MATCH", "LOW MATCH"],
            index=0,
            key="ai_status_select",
        )
        ai_overall_reported = st.number_input(
            "AI Reported Overall Score",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("ai_ov", 0.0)),
            step=1.0,
            format="%.2f",
            key="ai_overall_input",
            help="Exact overall score stated in the report (0–100).",
        )
        ai_keyword = st.number_input(
            "AI Keyword Match (25%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("ai_kw", 0.0)),
            step=1.0,
            format="%.2f",
            key="ai_keyword_input",
        )
        ai_skills = st.number_input(
            "AI Skills Coverage (25%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("ai_sk", 0.0)),
            step=1.0,
            format="%.2f",
            key="ai_skills_input",
        )
        ai_formatting = st.number_input(
            "AI ATS Formatting (15%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("ai_fmt", 0.0)),
            step=1.0,
            format="%.2f",
            key="ai_formatting_input",
        )
        ai_role = st.number_input(
            "AI Role Alignment (20%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("ai_role", 0.0)),
            step=1.0,
            format="%.2f",
            key="ai_role_input",
        )
        ai_impact = st.number_input(
            "AI Impact & Metrics (15%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("ai_imp", 0.0)),
            step=1.0,
            format="%.2f",
            key="ai_impact_input",
        )

    # Right Column: Human Resume Scores
    with col_human:
        st.markdown("#### 👤 Human-Written Resume")
        human_status = st.selectbox(
            "Human Status",
            options=["MODERATE MATCH", "STRONG MATCH", "WEAK MATCH", "LOW MATCH"],
            index=0,
            key="human_status_select",
        )
        human_overall_reported = st.number_input(
            "Human Reported Overall Score",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("human_ov", 0.0)),
            step=1.0,
            format="%.2f",
            key="human_overall_input",
            help="Exact human overall score stated in the report (0–100).",
        )
        human_keyword = st.number_input(
            "Human Keyword Match (25%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("human_kw", 0.0)),
            step=1.0,
            format="%.2f",
            key="human_keyword_input",
        )
        human_skills = st.number_input(
            "Human Skills Coverage (25%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("human_sk", 0.0)),
            step=1.0,
            format="%.2f",
            key="human_skills_input",
        )
        human_formatting = st.number_input(
            "Human ATS Formatting (15%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("human_fmt", 0.0)),
            step=1.0,
            format="%.2f",
            key="human_formatting_input",
        )
        human_role = st.number_input(
            "Human Role Alignment (20%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("human_role", 0.0)),
            step=1.0,
            format="%.2f",
            key="human_role_input",
        )
        human_impact = st.number_input(
            "Human Impact & Metrics (15%)",
            min_value=0.0,
            max_value=100.0,
            value=float(st.session_state.get("human_imp", 0.0)),
            step=1.0,
            format="%.2f",
            key="human_impact_input",
        )

    # ----------------------------------------------------
    # Center Column: Real-Time Live Calculations & Advantages
    # ----------------------------------------------------
    ai_calculated_overall = calculate_weighted_score(
        ai_keyword, ai_skills, ai_formatting, ai_role, ai_impact
    )
    human_calculated_overall = calculate_weighted_score(
        human_keyword, human_skills, human_formatting, human_role, human_impact
    )
    
    # Use reported score if entered > 0, otherwise fallback to calculated
    effective_ai_overall = ai_overall_reported if ai_overall_reported > 0 else (ai_calculated_overall or 0.0)
    effective_human_overall = human_overall_reported if human_overall_reported > 0 else (human_calculated_overall or 0.0)
    
    overall_adv = calculate_advantage(effective_ai_overall, effective_human_overall)
    rel_inc = calculate_relative_increase(effective_ai_overall, effective_human_overall)
    computed_winner = determine_winner(effective_ai_overall, effective_human_overall)

    with col_mid:
        st.markdown("#### ⚖️ Advantages")
        st.markdown("<div style='text-align: center; margin-top: 15px;'>", unsafe_allow_html=True)
        
        # Overall advantage big badge
        if overall_adv is not None:
            adv_color = "#10B981" if overall_adv > 0 else ("#EF4444" if overall_adv < 0 else "#64748B")
            adv_sign = "+" if overall_adv > 0 else ""
            st.metric(
                label="Overall Advantage",
                value=f"{adv_sign}{overall_adv:.1f}",
                delta=f"{rel_inc:+.1f}% vs Human" if rel_inc is not None else None,
            )
        else:
            st.metric(label="Overall Advantage", value="0.0")

        # Winner badge
        if computed_winner == "AI":
            st.success(f"🏆 Winner: **AI**")
        elif computed_winner == "HUMAN":
            st.warning(f"🏆 Winner: **HUMAN**")
        elif computed_winner == "TIE":
            st.info("🤝 Verdict: **TIE**")

        st.markdown("---")
        st.markdown("<small>**Category Diffs (AI − Human)**</small>", unsafe_allow_html=True)
        
        kw_diff = ai_keyword - human_keyword
        sk_diff = ai_skills - human_skills
        fmt_diff = ai_formatting - human_formatting
        role_diff = ai_role - human_role
        imp_diff = ai_impact - human_impact

        st.caption(f"Keyword: **{kw_diff:+.1f}**")
        st.caption(f"Skills: **{sk_diff:+.1f}**")
        st.caption(f"Formatting: **{fmt_diff:+.1f}**")
        st.caption(f"Role Fit: **{role_diff:+.1f}**")
        st.caption(f"Impact: **{imp_diff:+.1f}**")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------
    # Optional Qualitative & Raw Text Expander
    # ----------------------------------------------------
    with st.expander("📄 Optional: Qualitative Notes & Raw Report Text", expanded=False):
        qcol1, qcol2 = st.columns(2)
        with qcol1:
            ai_strengths = st.text_area("AI Resume Strengths", height=80)
            ai_weaknesses = st.text_area("AI Resume Weaknesses", height=80)
            winner_reasons = st.text_area("Winner Recommendation Reasons", height=80)
        with qcol2:
            human_strengths = st.text_area("Human Resume Strengths", height=80)
            human_weaknesses = st.text_area("Human Resume Weaknesses", height=80)
            raw_report = st.text_area("Raw Claude Chat Markdown (For Backup)", height=80)

    # ----------------------------------------------------
    # Action Bar: Save & Reset
    # ----------------------------------------------------
    st.markdown("---")
    btn_col1, btn_col2, btn_col3 = st.columns([2, 1, 3])

    with btn_col1:
        save_clicked = st.button("💾 Save Comparison Record", type="primary", width="stretch")
    with btn_col2:
        reset_clicked = st.button("🔄 Clear Form", width="stretch")

    # Handle Reset
    if reset_clicked:
        for key in ["ai_ov", "ai_kw", "ai_sk", "ai_fmt", "ai_role", "ai_imp",
                    "human_ov", "human_kw", "human_sk", "human_fmt", "human_role", "human_imp",
                    "entry_url"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Handle Save
    if save_clicked:
        # Validate data
        ai_cats = {
            "Keyword Match": ai_keyword,
            "Skills Coverage": ai_skills,
            "ATS Formatting": ai_formatting,
            "Role Alignment": ai_role,
            "Impact & Metrics": ai_impact,
        }
        human_cats = {
            "Keyword Match": human_keyword,
            "Skills Coverage": human_skills,
            "ATS Formatting": human_formatting,
            "Role Alignment": human_role,
            "Impact & Metrics": human_impact,
        }
        
        is_valid, issues = validate_manual_entry(
            model=selected_model,
            jd=selected_jd,
            ai_overall=ai_overall_reported,
            human_overall=human_overall_reported,
            ai_categories=ai_cats,
            human_categories=human_cats,
        )

        if not is_valid:
            for err in issues:
                st.error(f"❌ {err}")
            return

        # Check math consistency
        is_ai_math_consistent, _ = check_math_consistency(ai_overall_reported, ai_calculated_overall)
        is_human_math_consistent, _ = check_math_consistency(human_overall_reported, human_calculated_overall)
        is_math_consistent = is_ai_math_consistent and is_human_math_consistent

        # Build comparison record
        rec = ComparisonRecord(
            comparison_id=comparison_id.strip(),
            model=selected_model,
            jd=selected_jd,
            ai_status=ai_status,
            ai_overall_reported=ai_overall_reported if ai_overall_reported > 0 else ai_calculated_overall,
            ai_overall_calculated=ai_calculated_overall,
            ai_keyword_match=ai_keyword,
            ai_skills_coverage=ai_skills,
            ai_ats_formatting=ai_formatting,
            ai_role_alignment=ai_role,
            ai_impact_metrics=ai_impact,
            human_status=human_status,
            human_overall_reported=human_overall_reported if human_overall_reported > 0 else human_calculated_overall,
            human_overall_calculated=human_calculated_overall,
            human_keyword_match=human_keyword,
            human_skills_coverage=human_skills,
            human_ats_formatting=human_formatting,
            human_role_alignment=human_role,
            human_impact_metrics=human_impact,
            reported_ats_advantage=overall_adv,
            calculated_ats_advantage=overall_adv,
            relative_increase_percent=rel_inc,
            winner=computed_winner,
            ai_strengths=ai_strengths.strip() if 'ai_strengths' in locals() and ai_strengths else None,
            ai_weaknesses=ai_weaknesses.strip() if 'ai_weaknesses' in locals() and ai_weaknesses else None,
            human_strengths=human_strengths.strip() if 'human_strengths' in locals() and human_strengths else None,
            human_weaknesses=human_weaknesses.strip() if 'human_weaknesses' in locals() and human_weaknesses else None,
            winner_reasons=winner_reasons.strip() if 'winner_reasons' in locals() and winner_reasons else None,
            claude_chat_url=claude_url.strip() if claude_url else None,
            raw_report_text=raw_report.strip() if 'raw_report' in locals() and raw_report else None,
            is_math_consistent=is_math_consistent,
        )

        db.save_comparison(rec)
        st.toast(f"✅ Comparison '{comparison_id}' ({selected_model} on {selected_jd}) successfully saved!", icon="🎉")
        
        # Advance to next comparison ID
        next_id = db.get_next_comparison_id()
        st.session_state["entry_comp_id"] = next_id
        
        # Reset form score inputs
        for key in ["ai_ov", "ai_kw", "ai_sk", "ai_fmt", "ai_role", "ai_imp",
                    "human_ov", "human_kw", "human_sk", "human_fmt", "human_role", "human_imp",
                    "entry_url"]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()
