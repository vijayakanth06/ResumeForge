"""Model summary and leaderboard rankings with provisional status rules."""
from typing import Any, Dict, List
from config.settings import CONTROLLED_MODELS
from analysis.metrics import calculate_mean, calculate_std, calculate_win_rate


def generate_model_summary(comparisons: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregates comparisons across the 10 controlled models.
    Models with all 5 JDs completed receive official rank (1..N).
    Models with < 5 JDs are marked as Provisional (RANK = null / '-').
    """
    model_groups: Dict[str, List[Dict[str, Any]]] = {m: [] for m in CONTROLLED_MODELS}
    for c in comparisons:
        m = c["model"]
        if m in model_groups:
            model_groups[m].append(c)

    summary_list = []

    for model, records in model_groups.items():
        jd_count = len(records)
        jds_present = [r["jd"] for r in records]
        
        ai_overalls = [r["ai_overall_reported"] for r in records if r.get("ai_overall_reported") is not None]
        human_overalls = [r["human_overall_reported"] for r in records if r.get("human_overall_reported") is not None]
        advantages = [r["calculated_ats_advantage"] for r in records if r.get("calculated_ats_advantage") is not None]
        rel_increases = [r["relative_increase_percent"] for r in records if r.get("relative_increase_percent") is not None]
        
        # Category scores for AI
        ai_keywords = [r["ai_keyword_match"] for r in records if r.get("ai_keyword_match") is not None]
        ai_skills = [r["ai_skills_coverage"] for r in records if r.get("ai_skills_coverage") is not None]
        ai_formatting = [r["ai_ats_formatting"] for r in records if r.get("ai_ats_formatting") is not None]
        ai_role = [r["ai_role_alignment"] for r in records if r.get("ai_role_alignment") is not None]
        ai_impact = [r["ai_impact_metrics"] for r in records if r.get("ai_impact_metrics") is not None]

        winners = [r["winner"] for r in records]
        ai_wins, human_wins, ties, win_rate = calculate_win_rate(winners)

        is_complete = jd_count >= 5

        summary_list.append({
            "model": model,
            "jd_count": jd_count,
            "status": "Complete" if is_complete else f"Provisional ({jd_count}/5 JDs)",
            "is_complete": is_complete,
            "avg_advantage": calculate_mean(advantages),
            "std_advantage": calculate_std(advantages),
            "avg_relative_increase": calculate_mean(rel_increases),
            "avg_ai_overall": calculate_mean(ai_overalls),
            "avg_human_overall": calculate_mean(human_overalls),
            "avg_keyword_match": calculate_mean(ai_keywords),
            "avg_skills_coverage": calculate_mean(ai_skills),
            "avg_ats_formatting": calculate_mean(ai_formatting),
            "avg_role_alignment": calculate_mean(ai_role),
            "avg_impact_metrics": calculate_mean(ai_impact),
            "ai_wins": ai_wins,
            "human_wins": human_wins,
            "ties": ties,
            "win_rate_percent": win_rate,
        })

    # Sort complete models by avg_advantage descending, then provisional models by avg_advantage
    complete_models = sorted(
        [m for m in summary_list if m["is_complete"]],
        key=lambda x: x["avg_advantage"] if x["avg_advantage"] is not None else -999.0,
        reverse=True,
    )
    for rank, m in enumerate(complete_models, start=1):
        m["rank"] = rank

    provisional_models = sorted(
        [m for m in summary_list if not m["is_complete"]],
        key=lambda x: (x["jd_count"], x["avg_advantage"] if x["avg_advantage"] is not None else -999.0),
        reverse=True,
    )
    for m in provisional_models:
        m["rank"] = None  # Unranked until 5 JDs complete

    return complete_models + provisional_models
