"""Job Description level performance breakdown."""
from typing import Any, Dict, List
from config.settings import CONTROLLED_JDS
from analysis.metrics import calculate_mean, calculate_std, calculate_win_rate


def generate_jd_summary(comparisons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregates performance across each of the 5 Job Descriptions."""
    jd_groups: Dict[str, List[Dict[str, Any]]] = {j: [] for j in CONTROLLED_JDS}
    for c in comparisons:
        j = c["jd"]
        if j in jd_groups:
            jd_groups[j].append(c)

    summary_list = []
    for jd, records in jd_groups.items():
        advantages = [r["calculated_ats_advantage"] for r in records if r.get("calculated_ats_advantage") is not None]
        ai_overalls = [r["ai_overall_reported"] for r in records if r.get("ai_overall_reported") is not None]
        human_overalls = [r["human_overall_reported"] for r in records if r.get("human_overall_reported") is not None]
        winners = [r["winner"] for r in records]
        ai_wins, human_wins, ties, win_rate = calculate_win_rate(winners)

        summary_list.append({
            "jd": jd,
            "model_count": len(records),
            "avg_ai_score": calculate_mean(ai_overalls),
            "avg_human_score": calculate_mean(human_overalls),
            "avg_advantage": calculate_mean(advantages),
            "std_advantage": calculate_std(advantages),
            "ai_wins": ai_wins,
            "human_wins": human_wins,
            "ties": ties,
            "ai_win_rate_percent": win_rate,
        })

    return summary_list
