"""Database record dataclasses for ATS Resume Benchmark."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ComparisonRecord:
    """Master record for an ATS resume comparison run."""
    comparison_id: str
    model: str
    jd: str
    version: int = 1
    is_active: bool = True
    
    # AI Scores
    ai_status: str = "STRONG MATCH"
    ai_overall_reported: Optional[float] = None
    ai_overall_calculated: Optional[float] = None
    ai_keyword_match: Optional[float] = None
    ai_skills_coverage: Optional[float] = None
    ai_ats_formatting: Optional[float] = None
    ai_role_alignment: Optional[float] = None
    ai_impact_metrics: Optional[float] = None
    
    # Human Scores
    human_status: str = "MODERATE MATCH"
    human_overall_reported: Optional[float] = None
    human_overall_calculated: Optional[float] = None
    human_keyword_match: Optional[float] = None
    human_skills_coverage: Optional[float] = None
    human_ats_formatting: Optional[float] = None
    human_role_alignment: Optional[float] = None
    human_impact_metrics: Optional[float] = None
    
    # Comparison Metrics
    reported_ats_advantage: Optional[float] = None
    calculated_ats_advantage: Optional[float] = None
    relative_increase_percent: Optional[float] = None
    winner: str = "UNKNOWN"  # "AI", "HUMAN", "TIE", "UNKNOWN"
    
    # Qualitative Notes
    ai_strengths: Optional[str] = None
    ai_weaknesses: Optional[str] = None
    human_strengths: Optional[str] = None
    human_weaknesses: Optional[str] = None
    winner_reasons: Optional[str] = None
    
    # Audit & Metadata
    claude_chat_url: Optional[str] = None
    raw_report_text: Optional[str] = None
    is_math_consistent: bool = True
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
