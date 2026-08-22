"""JSON exporter generating structured hierarchical evaluation dataset."""
import json
from typing import Any, Dict, List
from config.settings import CONTROLLED_MODELS, CONTROLLED_JDS, CATEGORY_WEIGHTS


def export_comparisons_to_json(comparisons: List[Dict[str, Any]]) -> str:
    """Serializes dataset into structured nested JSON with metadata."""
    structured_records = []
    
    for c in comparisons:
        rec = {
            "comparison_id": c.get("comparison_id"),
            "model": c.get("model"),
            "jd": c.get("jd"),
            "version": c.get("version", 1),
            "ai_evaluation": {
                "status": c.get("ai_status"),
                "overall_reported": c.get("ai_overall_reported"),
                "overall_calculated": c.get("ai_overall_calculated"),
                "scores": {
                    "keyword_match": c.get("ai_keyword_match"),
                    "skills_coverage": c.get("ai_skills_coverage"),
                    "ats_formatting": c.get("ai_ats_formatting"),
                    "role_alignment": c.get("ai_role_alignment"),
                    "impact_metrics": c.get("ai_impact_metrics"),
                },
                "strengths": c.get("ai_strengths"),
                "weaknesses": c.get("ai_weaknesses"),
            },
            "human_evaluation": {
                "status": c.get("human_status"),
                "overall_reported": c.get("human_overall_reported"),
                "overall_calculated": c.get("human_overall_calculated"),
                "scores": {
                    "keyword_match": c.get("human_keyword_match"),
                    "skills_coverage": c.get("human_skills_coverage"),
                    "ats_formatting": c.get("human_ats_formatting"),
                    "role_alignment": c.get("human_role_alignment"),
                    "impact_metrics": c.get("human_impact_metrics"),
                },
                "strengths": c.get("human_strengths"),
                "weaknesses": c.get("human_weaknesses"),
            },
            "comparison_outcome": {
                "reported_ats_advantage": c.get("reported_ats_advantage"),
                "calculated_ats_advantage": c.get("calculated_ats_advantage"),
                "relative_increase_percent": c.get("relative_increase_percent"),
                "winner": c.get("winner"),
                "winner_reasons": c.get("winner_reasons"),
            },
            "audit_metadata": {
                "claude_chat_url": c.get("claude_chat_url"),
                "is_math_consistent": bool(c.get("is_math_consistent", 1)),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
            },
        }
        structured_records.append(rec)

    payload = {
        "metadata": {
            "title": "ATS Resume Benchmark — 50 Claude Comparisons",
            "total_records": len(comparisons),
            "target_total": 50,
            "controlled_models": CONTROLLED_MODELS,
            "controlled_jds": CONTROLLED_JDS,
            "weights": CATEGORY_WEIGHTS,
        },
        "comparisons": structured_records,
    }

    return json.dumps(payload, indent=2)
