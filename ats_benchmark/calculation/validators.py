"""Input validation and integrity checks for ATS Resume Benchmark."""
from typing import List, Optional, Tuple
from config.settings import CONTROLLED_MODELS, CONTROLLED_JDS, VALIDATION_TOLERANCE


def validate_score_range(score: Optional[float], name: str) -> Optional[str]:
    """Validates that a numerical score is within 0 to 100."""
    if score is not None:
        if score < 0.0 or score > 100.0:
            return f"Score '{name}' ({score}) is out of valid range 0–100."
    return None


def validate_manual_entry(
    model: str,
    jd: str,
    ai_overall: Optional[float],
    human_overall: Optional[float],
    ai_categories: dict,
    human_categories: dict,
) -> Tuple[bool, List[str]]:
    """
    Performs full data integrity checks on user manual entry.
    Returns: (is_valid, list_of_issues)
    """
    issues: List[str] = []

    # Model and JD validation
    if model not in CONTROLLED_MODELS:
        issues.append(f"Model '{model}' is not in controlled list of 10 models.")
    if jd not in CONTROLLED_JDS:
        issues.append(f"JD '{jd}' is not in controlled list (JD1-JD5).")

    # Range checks
    err = validate_score_range(ai_overall, "AI Overall Reported")
    if err:
        issues.append(err)
    err = validate_score_range(human_overall, "Human Overall Reported")
    if err:
        issues.append(err)

    for k, v in ai_categories.items():
        err = validate_score_range(v, f"AI {k}")
        if err:
            issues.append(err)

    for k, v in human_categories.items():
        err = validate_score_range(v, f"Human {k}")
        if err:
            issues.append(err)

    return len(issues) == 0, issues
