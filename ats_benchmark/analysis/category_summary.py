"""Category level comparison analysis across all evaluations."""
from typing import Any, Dict, List
from config.settings import CATEGORY_WEIGHTS
from analysis.metrics import calculate_mean, calculate_std


def generate_category_summary(comparisons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compares AI vs Human performance across the 5 standard categories."""
    categories = [
        ("Keyword Match (25%)", "ai_keyword_match", "human_keyword_match", 0.25),
        ("Skills Coverage (25%)", "ai_skills_coverage", "human_skills_coverage", 0.25),
        ("ATS-Safe Formatting (15%)", "ai_ats_formatting", "human_ats_formatting", 0.15),
        ("Role Alignment (20%)", "ai_role_alignment", "human_role_alignment", 0.20),
        ("Impact / Metrics (15%)", "ai_impact_metrics", "human_impact_metrics", 0.15),
    ]

    summary_list = []
    for cat_name, ai_col, human_col, weight in categories:
        ai_scores = [r[ai_col] for r in comparisons if r.get(ai_col) is not None]
        human_scores = [r[human_col] for r in comparisons if r.get(human_col) is not None]
        
        diffs = [
            round(r[ai_col] - r[human_col], 2)
            for r in comparisons
            if r.get(ai_col) is not None and r.get(human_col) is not None
        ]

        ai_mean = calculate_mean(ai_scores)
        human_mean = calculate_mean(human_scores)
        avg_diff = calculate_mean(diffs)

        ai_wins = sum(1 for d in diffs if d > 0)
        human_wins = sum(1 for d in diffs if d < 0)
        ties = sum(1 for d in diffs if d == 0)

        summary_list.append({
            "category": cat_name,
            "weight": weight,
            "avg_ai_score": ai_mean,
            "avg_human_score": human_mean,
            "avg_advantage": avg_diff,
            "std_advantage": calculate_std(diffs),
            "ai_wins": ai_wins,
            "human_wins": human_wins,
            "ties": ties,
        })

    return summary_list
