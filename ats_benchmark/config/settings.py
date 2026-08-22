"""Configuration settings and controlled vocabularies for ATS Resume Benchmark."""
import os
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent

# Exactly 10 Controlled Models
CONTROLLED_MODELS: List[str] = [
    "Gemini_3.6_flash",
    "Gemini_3.7_flash",
    "claude_sonnet_4.6",
    "claude_opus_4.6",
    "GPT_OSS_120B",
    "NVIDIA Nemotron 3 Nano 30B A3B",
    "gpt_oss : 20B",
    "cohere/north-mini-code",
    "Poolside Laguna S 2.1",
    "nvidia/nemotron-3-ultra-550b-a55b",
]

# Exactly 5 Controlled Job Descriptions
CONTROLLED_JDS: List[str] = [
    "JD1",
    "JD2",
    "JD3",
    "JD4",
    "JD5",
]

# Standard ATS Category weights for deterministic calculation
CATEGORY_WEIGHTS: Dict[str, float] = {
    "keyword_match": 0.25,
    "skills_coverage": 0.25,
    "ats_formatting": 0.15,
    "role_alignment": 0.20,
    "impact_metrics": 0.15,
}

# Maximum tolerance for rounding discrepancies between reported and calculated overall scores
VALIDATION_TOLERANCE: float = 1.0


class Settings:
    """Application configuration."""

    @property
    def database_path(self) -> Path:
        raw_path = os.getenv("DATABASE_PATH", "data/ats_benchmark.db")
        p = Path(raw_path)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p

    @property
    def backup_dir(self) -> Path:
        raw_path = os.getenv("BACKUP_DIR", "data/backups")
        p = Path(raw_path)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p


settings = Settings()
