"""Streamlit UI component: Dataset Explorer & Export Page."""
import pandas as pd
import streamlit as st

from config.settings import CONTROLLED_MODELS, CONTROLLED_JDS
from database.db import db
from export.csv_export import export_comparisons_to_csv
from export.json_export import export_comparisons_to_json
from export.xlsx_export import export_comparisons_to_xlsx


def render_dataset_page():
    """Renders the Dataset Explorer with search, filters, inspector, and downloads."""
    st.markdown("### 🗄️ Dataset Explorer & Exports")
    st.caption("Inspect, filter, edit, or export the verified ATS resume benchmark dataset.")

    all_records = db.get_all_active_comparisons()
    total_count = len(all_records)

    # ----------------------------------------------------
    # Top Stats & Export Buttons Bar
    # ----------------------------------------------------
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    stat_col1.metric("Total Records", f"{total_count} / 50")
    ai_wins = sum(1 for r in all_records if r.get("winner") == "AI")
    stat_col2.metric("AI Wins", f"{ai_wins} ({round(ai_wins/total_count*100, 1) if total_count else 0}%)")
    models_covered = len(set(r.get("model") for r in all_records))
    stat_col3.metric("Models Started", f"{models_covered} / 10")
    jds_covered = len(set(r.get("jd") for r in all_records))
    stat_col4.metric("JDs Evaluated", f"{jds_covered} / 5")

    st.markdown("---")

    # Export Bar
    st.markdown("##### 📥 Export Dataset")
    exp_col1, exp_col2, exp_col3, exp_col4 = st.columns([1.5, 1.5, 1.8, 1.5])
    
    if total_count > 0:
        csv_data = export_comparisons_to_csv(all_records)
        json_data = export_comparisons_to_json(all_records)
        xlsx_data = export_comparisons_to_xlsx(all_records)

        with exp_col1:
            st.download_button(
                label="📄 Download CSV (28 Cols)",
                data=csv_data,
                file_name="ats_resume_benchmark_28cols.csv",
                mime="text/csv",
                width="stretch",
            )
        with exp_col2:
            st.download_button(
                label="📦 Download JSON",
                data=json_data,
                file_name="ats_resume_benchmark.json",
                mime="application/json",
                width="stretch",
            )
        with exp_col3:
            st.download_button(
                label="📊 Download Excel (.xlsx, 6 Sheets)",
                data=xlsx_data,
                file_name="ats_resume_benchmark_workbook.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        with exp_col4:
            if st.button("💾 Backup SQLite DB", width="stretch"):
                backup_path = db.backup_database("manual_snapshot")
                st.success(f"Snapshot created: `{backup_path.name}`")
    else:
        st.info("No comparison records yet. Add your first record in the **Manual Entry** tab to enable exports.")

    st.markdown("---")

    # ----------------------------------------------------
    # Filter Bar
    # ----------------------------------------------------
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        model_filter = st.multiselect("Filter by Model", options=CONTROLLED_MODELS, default=[])
    with fcol2:
        jd_filter = st.multiselect("Filter by JD", options=CONTROLLED_JDS, default=[])
    with fcol3:
        winner_filter = st.multiselect("Filter by Winner", options=["AI", "HUMAN", "TIE"], default=[])

    filtered_records = all_records
    if model_filter:
        filtered_records = [r for r in filtered_records if r.get("model") in model_filter]
    if jd_filter:
        filtered_records = [r for r in filtered_records if r.get("jd") in jd_filter]
    if winner_filter:
        filtered_records = [r for r in filtered_records if r.get("winner") in winner_filter]

    st.markdown(f"**Showing {len(filtered_records)} of {total_count} records**")

    # ----------------------------------------------------
    # Table Display
    # ----------------------------------------------------
    if filtered_records:
        display_rows = []
        for r in filtered_records:
            adv = r.get("calculated_ats_advantage")
            adv_str = f"+{adv:.1f}" if adv is not None and adv > 0 else (f"{adv:.1f}" if adv is not None else "-")
            rel_inc = r.get("relative_increase_percent")
            rel_str = f"{rel_inc:+.1f}%" if rel_inc is not None else "-"
            
            display_rows.append({
                "ID": r.get("comparison_id"),
                "Model": r.get("model"),
                "JD": r.get("jd"),
                "Winner": r.get("winner"),
                "Advantage": adv_str,
                "Relative Inc %": rel_str,
                "AI Overall": r.get("ai_overall_reported"),
                "Human Overall": r.get("human_overall_reported"),
                "AI Keyword": r.get("ai_keyword_match"),
                "Human Keyword": r.get("human_keyword_match"),
                "AI Skills": r.get("ai_skills_coverage"),
                "Human Skills": r.get("human_skills_coverage"),
                "AI Formatting": r.get("ai_ats_formatting"),
                "Human Formatting": r.get("human_ats_formatting"),
                "AI Role": r.get("ai_role_alignment"),
                "Human Role": r.get("human_role_alignment"),
                "AI Impact": r.get("ai_impact_metrics"),
                "Human Impact": r.get("human_impact_metrics"),
                "Math Consistent": "✅" if r.get("is_math_consistent", 1) else "⚠️ Discrepancy",
            })
        
        df = pd.DataFrame(display_rows)
        st.dataframe(df, width="stretch", hide_index=True)

        # ----------------------------------------------------
        # Deep-Dive Record Inspector & Delete
        # ----------------------------------------------------
        st.markdown("---")
        st.markdown("##### 🔍 Record Inspector")
        selected_id = st.selectbox(
            "Select Comparison ID to Inspect or Delete",
            options=[r["comparison_id"] for r in filtered_records],
        )

        selected_rec = next((r for r in filtered_records if r["comparison_id"] == selected_id), None)
        if selected_rec:
            icol1, icol2 = st.columns(2)
            with icol1:
                st.markdown(f"**Model**: `{selected_rec.get('model')}` | **JD**: `{selected_rec.get('jd')}`")
                st.markdown(f"**Reported AI**: `{selected_rec.get('ai_overall_reported')}` (Calc: `{selected_rec.get('ai_overall_calculated')}`)")
                st.markdown(f"**Reported Human**: `{selected_rec.get('human_overall_reported')}` (Calc: `{selected_rec.get('human_overall_calculated')}`)")
                st.markdown(f"**Advantage**: `{selected_rec.get('calculated_ats_advantage')}` | **Winner**: `{selected_rec.get('winner')}`")
                if selected_rec.get("claude_chat_url"):
                    st.markdown(f"🔗 [Claude Chat Link]({selected_rec.get('claude_chat_url')})")
            
            with icol2:
                if selected_rec.get("ai_strengths"):
                    st.caption(f"**AI Strengths**: {selected_rec.get('ai_strengths')}")
                if selected_rec.get("human_strengths"):
                    st.caption(f"**Human Strengths**: {selected_rec.get('human_strengths')}")
                if selected_rec.get("winner_reasons"):
                    st.caption(f"**Winner Reasons**: {selected_rec.get('winner_reasons')}")

            # Delete button
            if st.button("🗑️ Delete Record", type="secondary"):
                db.delete_comparison(selected_id)
                st.toast(f"Record '{selected_id}' deleted.", icon="🗑️")
                st.rerun()
    else:
        st.info("No records match the selected filters.")
