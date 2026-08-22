"""Deterministic mathematical engine for ATS resume comparisons."""
from typing import Dict, Optional, Tuple
from config.settings import CATEGORY_WEIGHTS, VALIDATION_TOLERANCE


def calculate_weighted_score(
    keyword_match: Optional[float],
    skills_coverage: Optional[float],
    ats_formatting: Optional[float],
    role_alignment: Optional[float],
    impact_metrics: Optional[float],
) -> Optional[float]:
    """
    Deterministically computes the weighted ATS score using standard weights:
    Score = (Keyword * 0.25) + (Skills * 0.25) + (Formatting * 0.15) + (Role * 0.20) + (Impact * 0.15)
    """
    scores = {
        "keyword_match": keyword_match,
        "skills_coverage": skills_coverage,
        "ats_formatting": ats_formatting,
        "role_alignment": role_alignment,
        "impact_metrics": impact_metrics,
    }
    
    # If any score is missing, return None
    if any(v is None for v in scores.values()):
        return None
    
    total = sum(scores[cat] * CATEGORY_WEIGHTS[cat] for cat in CATEGORY_WEIGHTS)
    return round(total, 2)


def calculate_advantage(ai_score: Optional[float], human_score: Optional[float]) -> Optional[float]:
    """Computes overall advantage: AI Score - Human Score."""
    if ai_score is None or human_score is None:
        return None
    return round(ai_score - human_score, 2)


def calculate_relative_increase(ai_score: Optional[float], human_score: Optional[float]) -> Optional[float]:
    """
    Computes percentage increase towards human score:
    ((AI - Human) / Human) * 100
    """
    if ai_score is None or human_score is None or human_score <= 0:
        return None
    return round(((ai_score - human_score) / human_score) * 100.0, 2)


def determine_winner(ai_score: Optional[float], human_score: Optional[float]) -> str:
    """Deterministically identifies the winner based on scores."""
    if ai_score is None or human_score is None:
        return "UNKNOWN"
    if ai_score > human_score:
        return "AI"
    elif human_score > ai_score:
        return "HUMAN"
    else:
        return "TIE"


def check_math_consistency(
    reported: Optional[float],
    calculated: Optional[float],
    tolerance: float = VALIDATION_TOLERANCE,
) -> Tuple[bool, Optional[str]]:
    """Checks if reported overall matches calculated weighted score within tolerance."""
    if reported is None or calculated is None:
        return True, None
    diff = abs(reported - calculated)
    if diff > tolerance:
        return False, f"Reported score ({reported}) differs from calculated weighted score ({calculated}) by {diff:.2f} points."
    elif diff > 0:
        return True, f"Minor rounding difference: reported {reported} vs calculated {calculated} (diff: {diff:.2f})."
    return True, None
