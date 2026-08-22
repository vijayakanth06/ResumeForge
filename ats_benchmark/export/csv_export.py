"""CSV exporter generating the exact 28-column evaluation dataset."""
import csv
import io
from typing import Any, Dict, List

# Exact 28 Research Dataset Columns
CSV_28_COLUMNS = [
    "comparison_id",
    "model",
    "jd",
    "ai_status",
    "ai_overall_reported",
    "ai_overall_calculated",
    "ai_keyword_match",
    "ai_skills_coverage",
    "ai_ats_formatting",
    "ai_role_alignment",
    "ai_impact_metrics",
    "human_status",
    "human_overall_reported",
    "human_overall_calculated",
    "human_keyword_match",
    "human_skills_coverage",
    "human_ats_formatting",
    "human_role_alignment",
    "human_impact_metrics",
    "reported_ats_advantage",
    "calculated_ats_advantage",
    "relative_increase_percent",
    "winner",
    "ai_strengths",
    "ai_weaknesses",
    "human_strengths",
    "human_weaknesses",
    "claude_chat_url",
]


def export_comparisons_to_csv(comparisons: List[Dict[str, Any]]) -> str:
    """Serializes comparison records into exact 28-column CSV format."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_28_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in comparisons:
        writer.writerow(row)
    return output.getvalue()
