"""Statistical calculation utilities for ATS Benchmark analysis."""
import math
from typing import List, Optional, Tuple


def calculate_mean(values: List[float]) -> Optional[float]:
    """Computes arithmetic mean of a list of floats."""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)


def calculate_std(values: List[float]) -> Optional[float]:
    """Computes sample standard deviation of a list of floats."""
    valid = [v for v in values if v is not None]
    if len(valid) < 2:
        return 0.0 if len(valid) == 1 else None
    mean = sum(valid) / len(valid)
    variance = sum((x - mean) ** 2 for x in valid) / (len(valid) - 1)
    return round(math.sqrt(variance), 2)


def calculate_win_rate(winners: List[str]) -> Tuple[int, int, int, float]:
    """
    Computes counts and percentage win rate for AI.
    Returns: (ai_wins, human_wins, ties, win_rate_percent)
    """
    ai_wins = sum(1 for w in winners if w == "AI")
    human_wins = sum(1 for w in winners if w == "HUMAN")
    ties = sum(1 for w in winners if w == "TIE")
    total = len(winners)
    win_rate = round((ai_wins / total) * 100.0, 1) if total > 0 else 0.0
    return ai_wins, human_wins, ties, win_rate
