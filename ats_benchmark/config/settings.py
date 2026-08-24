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

# Detailed Job Description metadata extracted from benchmark files
JD_METADATA: Dict[str, Dict[str, str]] = {
    "JD1": {
        "company": "Josh Technology Group",
        "role": "Software Developer (Intern)",
        "short_label": "JD1: Josh Tech (SWE)",
        "full_title": "Josh Technology Group — Software Developer",
        "domain": "Product Engineering / Multi-domain",
        "experience": "0 yrs (2027 batch)",
        "stipend_salary": "Stipend: ₹22,500/mo, CTC: ₹15.47 LPA",
        "key_tech": "Java, Python, Django, Ruby on Rails, Groovy, PostgreSQL, MySQL, CouchDB, Maven",
        "location": "Gurugram, India",
    },
    "JD2": {
        "company": "Cisco",
        "role": "Software Engineer – AI Software & Platform",
        "short_label": "JD2: Cisco (AI Platform)",
        "full_title": "Cisco — Software Engineer (AI Software & Platform)",
        "domain": "AI / Cloud Infrastructure / Distributed Systems",
        "experience": "0–2 yrs",
        "stipend_salary": "Competitive Industry Standard",
        "key_tech": "Go, Python, MCP, Agentic AI, Docker, Kubernetes, MySQL, Redis, Microservices, Networking",
        "location": "Global / Remote",
    },
    "JD3": {
        "company": "Kuku FM",
        "role": "Backend Developer",
        "short_label": "JD3: Kuku FM (Backend)",
        "full_title": "Kuku FM — Backend Developer",
        "domain": "Media / OTT / Audio Storytelling Platform",
        "experience": "0–1 yrs",
        "stipend_salary": "Competitive Startup Standard",
        "key_tech": "Java, Python, Spring Boot, FastAPI, Django, MySQL, PostgreSQL, REST APIs, Git",
        "location": "India / Remote",
    },
    "JD4": {
        "company": "Revolte",
        "role": "Full Stack Software Engineer I",
        "short_label": "JD4: Revolte (Full Stack)",
        "full_title": "Revolte — Full Stack Software Engineer I",
        "domain": "AI for Software Engineering / DevOps",
        "experience": "1–3 yrs",
        "stipend_salary": "Competitive Startup Equity + CTC",
        "key_tech": "React, Next.js, TypeScript, Node.js, FastAPI, PostgreSQL, Docker, K8s, OpenAI/Claude APIs, RAG",
        "location": "AI Startup / Remote",
    },
    "JD5": {
        "company": "Springreen",
        "role": "Full Stack Developer Trainee",
        "short_label": "JD5: Springreen (MERN/MEAN)",
        "full_title": "Springreen — Full Stack Developer Trainee (MERN/MEAN)",
        "domain": "Enterprise Software & AI Integrations",
        "experience": "0 yrs (2023–2026 batch)",
        "stipend_salary": "₹4.25 LPA – ₹6.00 LPA",
        "key_tech": "React.js, Node.js, Express, Python, Django, MongoDB, MySQL, PostgreSQL, AWS, Docker",
        "location": "Pan India",
    },
}

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
