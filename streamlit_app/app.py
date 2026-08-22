"""
ResumeForge ATS Studio — Streamlit Application (OpenRouter & Multi-Provider)
============================================================================
Standalone, modern Streamlit web application powered by OpenRouter API
and ResumeForge MCP Tools for ultra-high-powered ATS resume generation,
scoring, and interactive conversational optimization.
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from openai import OpenAI

# ─────────────────────────────────────────────────────────────────────────────
# 1. Path Setup & Environment Loading
# ─────────────────────────────────────────────────────────────────────────────

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent if (CURRENT_DIR.parent / "server.py").exists() else CURRENT_DIR

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Attempt to load .env from project root or current dir
try:
    from dotenv import load_dotenv
    if (PROJECT_ROOT / ".env").exists():
        load_dotenv(PROJECT_ROOT / ".env")
    elif (CURRENT_DIR / ".env").exists():
        load_dotenv(CURRENT_DIR / ".env")
except ImportError:
    pass

# Try importing ResumeForge MCP tool directly if available
try:
    from tailor_mcp.tool import tailor_resume_for_job as rf_tailor_resume_for_job
    from tailor_mcp.reader import read_all_md_files, read_jd_from_file
    HAS_LOCAL_MCP = True
except Exception:
    HAS_LOCAL_MCP = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_app")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Page Configuration & Custom CSS Styling
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ResumeForge ATS Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* Modern Dark Glassmorphism Theme */
:root {
    --primary-color: #6366f1;
    --primary-hover: #4f46e5;
    --bg-card: rgba(30, 41, 59, 0.7);
    --border-color: rgba(255, 255, 255, 0.1);
    --text-muted: #94a3b8;
    --accent-green: #10b981;
    --accent-amber: #f59e0b;
    --accent-red: #ef4444;
}

.main-header {
    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.3rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
    letter-spacing: -0.5px;
}

.sub-header {
    color: #94a3b8;
    font-size: 1rem;
    margin-bottom: 1.5rem;
}

.glass-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.metric-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.9));
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}

.metric-val {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0.2rem 0;
}

.badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.15rem;
}
.badge-green {
    background-color: rgba(16, 185, 129, 0.2);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.4);
}
.badge-amber {
    background-color: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
}
.badge-red {
    background-color: rgba(239, 68, 68, 0.2);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
}

.resume-preview-box {
    background: #0f172a;
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 2rem;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.6;
    max-height: 700px;
    overflow-y: auto;
}

.mcp-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #a5b4fc;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 500;
}

.token-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #34d399;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 500;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. File Extractors & Biography Prioritizers
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_file_bytes(file_name: str, file_bytes: bytes) -> str:
    """Extract raw text from uploaded bytes (PDF, DOCX, TXT, MD)."""
    suffix = Path(file_name).suffix.lower()
    
    if suffix in (".txt", ".md"):
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="replace")
            
    elif suffix == ".pdf":
        text_parts = []
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    p_text = page.extract_text()
                    if p_text:
                        text_parts.append(p_text)
            if text_parts:
                return "\n".join(text_parts).strip()
        except Exception:
            pass
            
        try:
            import fitz
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            if text_parts:
                return "\n".join(text_parts).strip()
        except Exception as e:
            logger.warning("PDF extraction failed: %s", e)
            
    elif suffix == ".docx":
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs).strip()
        except Exception as e:
            logger.warning("DOCX extraction failed: %s", e)
            
    return ""


def extract_files_from_zip(zip_bytes: bytes) -> Dict[str, str]:
    """Extract markdown/text files from a zip archive."""
    extracted = {}
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for file_info in z.infolist():
                if not file_info.is_dir() and file_info.filename.endswith((".md", ".txt")):
                    content = z.read(file_info).decode("utf-8", errors="replace")
                    if content.strip():
                        extracted[file_info.filename] = content
    except Exception as e:
        logger.warning("Zip extraction error: %s", e)
    return extracted


def load_repository_md_files(md_dir: Optional[Path] = None) -> Dict[str, str]:
    """Scan and read all raw markdown files from the workspace md/ directory."""
    if md_dir is None:
        md_dir = PROJECT_ROOT / "md"
        
    if not md_dir.exists() or not md_dir.is_dir():
        return {}
        
    files = {}
    for md_file in sorted(md_dir.rglob("*.md")):
        if "tailored" in md_file.parts:
            continue
        try:
            rel = str(md_file.relative_to(md_dir))
            content = md_file.read_text(encoding="utf-8").strip()
            if content:
                files[rel] = content
        except Exception as e:
            logger.warning("Failed to read %s: %s", md_file, e)
            
    return files


def build_smart_biography(
    all_files: Dict[str, str],
    jd_text: str = "",
    mode: str = "smart",
) -> Tuple[str, int]:
    """
    Aggregates candidate files into a clean biography string.
    
    Modes:
      - 'smart' (~4k tokens): Core LinkedIn/Bio files + Top 6 JD-matched projects.
      - 'balanced' (~8k tokens): Core files + Top 15 JD-matched projects + resume history.
      - 'full' (15k-25k+ tokens): Unconditionally includes all 60+ source files.
    """
    if not all_files:
        return "", 0

    if mode == "full":
        parts = [f"══════ FILE: {rel} ══════\n{content}" for rel, content in all_files.items()]
        combined = "\n\n".join(parts)
        return combined, len(combined) // 4

    core_parts: List[str] = []
    project_candidates: List[Tuple[str, str, int]] = []
    jd_words = set(re.findall(r"\b[A-Za-z0-9+#.-]{3,}\b", jd_text.lower())) if jd_text else set()

    for rel, content in all_files.items():
        rel_norm = rel.replace("\\", "/").lower()
        
        if any(key in rel_norm for key in [
            "identity.md", "summary.md", "skills.md", "experience.md",
            "education.md", "certifications.md", "coding/", "projects_summary.md"
        ]):
            core_parts.append(f"══════ FILE: {rel} ══════\n{content}")
            
        elif "resume_history.md" in rel_norm:
            if mode == "smart":
                trimmed_res = content[:3000] + ("\n... [Older history omitted for brevity]" if len(content) > 3000 else "")
                core_parts.append(f"══════ FILE: {rel} (Recent Highlights) ══════\n{trimmed_res}")
            else:
                core_parts.append(f"══════ FILE: {rel} ══════\n{content}")
                
        elif "projects/" in rel_norm or "projects.md" in rel_norm:
            content_lower = content.lower()
            match_score = sum(1 for w in jd_words if w in content_lower)
            project_candidates.append((rel, content, match_score))
        else:
            project_candidates.append((rel, content, 0))

    project_candidates.sort(key=lambda x: x[2], reverse=True)
    num_projects = 6 if mode == "smart" else 15
    selected_projects = project_candidates[:num_projects]

    for rel, content, score in selected_projects:
        core_parts.append(f"══════ FILE: {rel} (Relevance Score: {score}) ══════\n{content}")

    combined = "\n\n".join(core_parts)
    est_tokens = len(combined) // 4
    return combined, est_tokens


# ─────────────────────────────────────────────────────────────────────────────
# 4. High-Powered ATS Prompt & Engine
# ─────────────────────────────────────────────────────────────────────────────

HIGH_POWERED_ATS_SYSTEM_PROMPT = """
You are an Elite Executive Resume Strategist and ATS (Applicant Tracking System) Optimization Engine.
You specialize in compiling 95%+ ATS-compatible resumes that flawlessly pass enterprise parsers (Taleo, Greenhouse, Workday, Lever, iCIMS) while compelling human hiring managers.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL OUTPUT DIRECTIVES (MUST OBEY):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Output ONLY the single final Markdown resume text.
2. DO NOT output any introduction, conversational preamble, thinking process, step-by-step analysis, explanation, breakdown of requirements, draft notes, or postscript.
3. Start IMMEDIATELY on line 1 with the candidate's full name as an H1 heading: `# VIJAYAKANTH M`.
4. STRICT ONE-PAGE CONSTRAINT: The entire resume MUST strictly fit onto ONE single physical page. Keep every section compact, ultra-concise, and high-impact. Do NOT calculate words, count tokens, plan drafts, or write meta-commentary.
5. The output must be ready to save directly as a .md file.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRICT 1-PAGE SECTION ARCHITECTURE & BUDGET:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **IDENTITY / HEADER** (1 line name + 1 line contact):
   `# Full Name`
   `Email | Phone | LinkedIn | GitHub | Location`

2. **PROFESSIONAL SUMMARY** (Strictly 2-3 lines max):
   - A razor-sharp 2-3 line executive summary integrating target Job Title, years of experience, core technical capabilities, and top 4-5 JD keywords.

3. **TECHNICAL SKILLS** (Strictly 4-5 concise lines):
   - Group into categories: `Languages`, `Frameworks & Libraries`, `Cloud & DevOps`, `Databases & Storage`, `AI/ML & Tools`.
   - Place JD-critical keywords first in each category.

4. **WORK EXPERIENCE** (Top 2-3 relevant roles, strictly 2-3 bullets per role):
   - Format: `### Job Title | Company Name | Dates`
   - Use Google's X-Y-Z formula (*"Accomplished [X], measured by [Y], by doing [Z]"*).
   - High-impact action verbs, quantified results, single-line bullets to preserve 1-page layout.

5. **KEY PROJECTS** (Select at most 4 projects — top 2 to 4 most JD-relevant projects):
   - Format: `### Project Title | [Link/Repo]`
   - Line 1: `**Tech Stack:** React, Python, Docker, FastAPI`
   - Strictly 1-2 concise, result-driven bullets per project.

6. **EDUCATION** (Strictly 1-2 compact lines):
   - `**Degree in Major** | University / Institution | CGPA/GPA | Graduation Year`

7. **CERTIFICATIONS & ACHIEVEMENTS** (Strictly 2-3 bullet lines):
   - Top verified credentials, hackathon wins, or key technical honors.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ATS FORMAT & PARSING COMPLIANCE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Semantic Markdown headings:
  `# Candidate Name`
  `Email | Phone | LinkedIn | GitHub | Location`
  `## Professional Summary`
  `## Skills`
  `## Work Experience`
  `## Key Projects`
  `## Education`
  `## Certifications & Achievements`
- Use standard bullet points (`- `).
- No complex tables, text boxes, emojis, or nested graphics that choke ATS parsers.
- Truthful & Grounded: Strictly source all facts from the candidate biography data. Never fabricate.
""".strip()


def extract_clean_single_resume(raw_text: str) -> str:
    """Extract strictly the single final markdown resume, removing thoughts and preambles."""
    if not raw_text:
        return ""

    # 1. Remove <think>...</think> blocks from reasoning models
    cleaned = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()

    # 2. Extract code block if wrapped in markdown fences
    if "```" in cleaned:
        lines = cleaned.split("\n")
        inside_fence = False
        fence_lines = []
        for line in lines:
            if line.strip().startswith("```"):
                inside_fence = not inside_fence
                continue
            if inside_fence:
                fence_lines.append(line)
        if fence_lines:
            cleaned = "\n".join(fence_lines).strip()

    # 3. Strip any preamble or step-by-step thinking traces before the candidate name / header
    patterns = [
        r"(?:^|\n)(#[ \t]+[^\r\n]{2,})",
        r"(?:^|\n)(##[ \t]+(?:Professional\s+Summary|Summary|Contact|Identity))",
    ]
    for pat in patterns:
        m = re.search(pat, cleaned, flags=re.IGNORECASE)
        if m:
            start_idx = m.start(1) if m.lastindex else m.start()
            candidate_slice = cleaned[start_idx:].strip()
            if "##" in candidate_slice:
                cleaned = candidate_slice
                break

    # 4. Remove any postscripts or closing chatter (including word-counting / drafting monologue)
    post_patterns = [
        r"\n+(?:---\n+)?(?:Note:|Explanation:|Let me know if|I hope this helps|Draft:|Now count words|Let's count|Total words|Let's calculate|Let's approximate|We need to reach|We need to add|We need to increase|Now approximate|Word count|Approximate word|I'll draft|I will draft|Header line:|Contact line:)",
    ]
    for p_pat in post_patterns:
        pm = re.search(p_pat, cleaned, flags=re.IGNORECASE)
        if pm:
            cleaned = cleaned[:pm.start()].strip()

    return cleaned.strip()


def calculate_ats_metrics(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """Calculate ATS match score, keyword density, matched & missing keywords."""
    if not resume_text or not jd_text:
        return {"score": 0, "matched": [], "missing": [], "total_jd_keywords": 0}
        
    common_stopwords = {
        "and", "the", "with", "for", "that", "this", "from", "have", "will", "your",
        "our", "team", "work", "role", "looking", "must", "years", "experience",
        "ability", "strong", "skills", "good", "knowledge", "working", "responsibilities",
        "requirements", "plus", "preferred", "including", "using", "such", "into", "across",
        "about", "also", "well", "closely", "join", "help", "build", "create", "support",
        "candidate", "ideal", "opportunity", "qualifications", "required", "equal", "employer"
    }
    
    raw_words = re.findall(r"\b[A-Za-z0-9+#.-]{2,}\b", jd_text.lower())
    jd_keywords = set()
    for w in raw_words:
        if len(w) > 2 and w not in common_stopwords and not w.isdigit():
            jd_keywords.add(w)
            
    tech_patterns = [
        "python", "javascript", "typescript", "react", "next.js", "node.js", "fastapi",
        "django", "flask", "docker", "kubernetes", "aws", "gcp", "azure", "sql", "postgresql",
        "mongodb", "redis", "graphql", "rest api", "ci/cd", "git", "linux", "machine learning",
        "deep learning", "llm", "mcp", "pytorch", "tensorflow", "agile", "scrum", "microservices",
        "terraform", "kafka", "pandas", "numpy", "c++", "golang", "java", "spring boot", "rust"
    ]
    for tech in tech_patterns:
        if tech in jd_text.lower():
            jd_keywords.add(tech)
            
    resume_lower = resume_text.lower()
    matched = []
    missing = []
    
    for kw in sorted(jd_keywords):
        if kw in resume_lower:
            matched.append(kw)
        else:
            missing.append(kw)
            
    total = len(jd_keywords)
    score = int((len(matched) / total * 100)) if total > 0 else 70
    score = min(max(score, 25), 98)
    
    return {
        "score": score,
        "matched": matched[:40],
        "missing": missing[:30],
        "total_jd_keywords": total,
        "matched_count": len(matched),
        "missing_count": len(missing),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. OpenRouter / OpenAI & MCP Tool Bridge
# ─────────────────────────────────────────────────────────────────────────────

OPENROUTER_DEFAULT_MODELS = [
    # ── Google Suite (Free & Large Context) ──
    ("google/gemma-4-31b-it:free", "🔵 Google Gemma 4 31B (Free — 262k Context, Top ATS Formatting)"),
    ("google/gemma-4-26b-a4b-it:free", "🔵 Google Gemma 4 26B A4B (Free — 262k Context)"),
    ("google/lyria-3-pro-preview", "🔵 Google Lyria 3 Pro (Free — 1,048,576 Context, 1M Tokens)"),
    ("google/gemini-2.0-flash-exp:free", "🔵 Google Gemini 2.0 Flash Exp (Free — 1,048,576 Context)"),
    
    # ── Meta Llama Suite (Free & Large Context) ──
    ("meta-llama/llama-3.3-70b-instruct:free", "🟠 Meta LLaMA 3.3 70B Instruct (Free — 131k Context)"),
    ("meta-llama/llama-3.1-8b-instruct:free", "🟠 Meta LLaMA 3.1 8B Instruct (Free — 131k Context)"),
    ("meta-llama/llama-3.2-3b-instruct:free", "🟠 Meta LLaMA 3.2 3B Instruct (Free — 131k Context)"),
    
    # ── Qwen & Alibaba Suite (Free & Large Context) ──
    ("qwen/qwen-2.5-72b-instruct:free", "🟣 Qwen 2.5 72B Instruct (Free — 131k Context, Top Benchmark)"),
    ("qwen/qwen-2.5-coder-32b-instruct:free", "🟣 Qwen 2.5 Coder 32B (Free — 131k Context, Coding/Tech Focus)"),
    ("qwen/qwen-2.5-7b-instruct:free", "🟣 Qwen 2.5 7B Instruct (Free — 131k Context)"),
    
    # ── Mistral AI Suite (Free) ──
    ("mistralai/mistral-7b-instruct:free", "🟢 Mistral 7B Instruct (Free — 32k Context)"),
    ("mistralai/mistral-nemo:free", "🟢 Mistral Nemo 12B (Free — 128k Context)"),
    
    # ── NVIDIA Nemotron Suite (Free & Massive Context) ──
    ("nvidia/nemotron-3-ultra-550b-a55b:free", "🧠 NVIDIA Nemotron 3 Ultra 550B (Free — 1,000,000 Context, Recommended Flagship)"),
    ("nvidia/nemotron-3.5-lightning:free", "⚡ NVIDIA Nemotron 3.5 Lightning (Free — 1,000,000 Context, 55 t/s)"),
    ("nvidia/nemotron-3-nano-30b-a3b:free", "⚡ NVIDIA Nemotron 3 Nano 30B A3B (Free — 256k Context)"),
    ("nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "🔬 NVIDIA Nemotron 3 Nano Omni Reasoning (Free — 256k Context)"),
    ("nvidia/nemotron-3-super-120b-a12b:free", "💎 NVIDIA Nemotron 3 Super 120B (Free — 262k Context)"),
    ("nvidia/nemotron-nano-12b-v2-vl:free", "⚡ NVIDIA Nemotron Nano 12B V2 (Free — 128k Context)"),
    ("nvidia/nemotron-nano-9b-v2:free", "⚡ NVIDIA Nemotron Nano 9B V2 (Free — 128k Context)"),
    
    # ── Other High-Context Free Open-Source Models ──
    ("cohere/north-mini-code:free", "💻 Cohere North Mini Code (Free — 256k Context, Tech & Code Specialist)"),
    ("poolside/laguna-s-2.1:free", "🌊 Poolside Laguna S 2.1 (Free — 262k Context, Direct Clean Output)"),
    ("poolside/laguna-xs-2.1:free", "🌊 Poolside Laguna XS 2.1 (Free — 262k Context)"),
    ("z-ai/glm-5.2:free", "⚡ Z.ai GLM 5.2 (Free — 256k Context, 135 t/s)"),
    ("dots-studio/dots-3-note-preview:free", "📝 Dots Studio Note Preview (Free — 512k Context)"),
    ("openai/gpt-oss-20b:free", "🤖 OpenAI gpt-oss-20b (Free — 131k Context)"),
    ("liquid/lfm-2.5-2.6b:free", "💧 LiquidAI LFM 2.5 2.6B (Free — 65k Context)"),
    ("stealth/ox-alpha", "🛡️ Stealth Ox Alpha (Free — 1,048,576 Context, 1M Tokens)"),
    ("openrouter/free", "🌟 OpenRouter Free Router (Auto-selects active free model)"),
    
    # ── Official & Paid Models ──
    ("deepseek/deepseek-r1", "DeepSeek R1 (Paid / Official)"),
    ("meta-llama/llama-3.3-70b-instruct", "LLaMA 3.3 70B (Paid / Official)"),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
    ("openai/gpt-4o", "OpenAI GPT-4o"),
    ("google/gemini-2.0-flash-001", "Google Gemini 2.0 Flash"),
    ("mistralai/mistral-large-2411", "Mistral Large 2411"),
]


@st.cache_data(ttl=1800)
def fetch_live_openrouter_free_models() -> List[Tuple[str, str]]:
    """Dynamically query OpenRouter API for currently active free models and merge with defaults."""
    import urllib.request
    try:
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/models",
            headers={"User-Agent": "ResumeForgeATS/1.0"}
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            live_free = []
            seen_ids = set()
            for m in data.get("data", []):
                m_id = m.get("id", "")
                pricing = m.get("pricing", {})
                prompt_price = float(pricing.get("prompt", 0) or 0)
                compl_price = float(pricing.get("completion", 0) or 0)
                if ":free" in m_id or (prompt_price == 0 and compl_price == 0):
                    ctx = m.get("context_length", 0)
                    name = m.get("name", m_id)
                    label = f"🆓 {name} ({ctx:,} ctx)"
                    live_free.append((m_id, label))
                    seen_ids.add(m_id)
            
            # Merge existing curated models that may not be in live list
            for m_id, label in OPENROUTER_DEFAULT_MODELS:
                if m_id not in seen_ids:
                    live_free.append((m_id, label))
            if live_free:
                return live_free
    except Exception as e:
        logger.debug("Failed to fetch live OpenRouter models: %s", e)
    return OPENROUTER_DEFAULT_MODELS

MCP_FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tailor_resume_for_job",
            "description": "Executes the ResumeForge MCP tool to aggregate candidate biography data and generate an ATS-optimized tailored resume context for the given Job Description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_description_text": {
                        "type": "string",
                        "description": "The target job description text to tailor against.",
                    },
                    "target_role": {
                        "type": "string",
                        "description": "Optional target company and role title, e.g. 'Google Software Engineer'.",
                    },
                },
                "required": ["job_description_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_ats_compatibility",
            "description": "Evaluates a resume draft against the target Job Description to determine keyword match score and missing competencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "resume_text": {
                        "type": "string",
                        "description": "The Markdown resume text.",
                    },
                    "job_description": {
                        "type": "string",
                        "description": "The Job Description text.",
                    },
                },
                "required": ["resume_text", "job_description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_tailored_resume",
            "description": "Saves the generated ATS resume Markdown file to the workspace md/tailored/ directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename formatted as Company_Role.md (e.g. Google_SoftwareEngineer.md).",
                    },
                    "content": {
                        "type": "string",
                        "description": "The complete markdown resume content.",
                    },
                },
                "required": ["filename", "content"],
            },
        },
    },
]


def execute_mcp_tool_locally(tool_name: str, arguments: Dict[str, Any], context_bio: str) -> str:
    """Locally execute the ResumeForge MCP tool requested by the LLM."""
    try:
        if tool_name == "tailor_resume_for_job":
            jd_text = arguments.get("job_description_text", "")
            if HAS_LOCAL_MCP:
                try:
                    return rf_tailor_resume_for_job(job_description_text=jd_text)
                except Exception:
                    pass
            return f"Aggregated candidate biography ({len(context_bio)} chars) with target JD ({len(jd_text)} chars)."

        elif tool_name == "analyze_ats_compatibility":
            res_text = arguments.get("resume_text", "")
            jd_text = arguments.get("job_description", "")
            metrics = calculate_ats_metrics(res_text, jd_text)
            return json.dumps(metrics, indent=2)

        elif tool_name == "save_tailored_resume":
            fname = arguments.get("filename", "Tailored_Resume.md")
            content = arguments.get("content", "")
            if not fname.endswith(".md"):
                fname += ".md"
            out_dir = PROJECT_ROOT / "md" / "tailored"
            out_dir.mkdir(parents=True, exist_ok=True)
            target_path = out_dir / fname
            target_path.write_text(content, encoding="utf-8")
            return f"Successfully saved tailored resume to {target_path.relative_to(PROJECT_ROOT)}"

    except Exception as e:
        return f"Error executing tool {tool_name}: {e}"

    return f"Tool {tool_name} not found."


FALLBACK_FREE_MODELS = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-nano-30b-a3b:free",
    "poolside/laguna-s-2.1:free",
    "google/gemma-4-26b-a4b-it:free",
    "z-ai/glm-5.2:free",
    "openrouter/free",
]


def call_llm_api(
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.1,
    enable_tools: bool = False,
    base_url: str = "https://openrouter.ai/api/v1",
) -> Tuple[str, Optional[List[Dict[str, Any]]], str]:
    """
    Execute LLM call using OpenAI-compatible client.
    Includes smart auto-fallback across high-context free models if upstream provider 429/404/503 occurs.
    Returns: (content, tool_calls, actual_model_used)
    """
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        default_headers={
            "HTTP-Referer": "https://github.com/vijayakanth06/ResumeForge",
            "X-Title": "ResumeForge ATS Studio",
        },
    )

    # Prepare model fallback candidates if using OpenRouter
    if "openrouter.ai" in base_url.lower():
        models_to_try = [model] + [m for m in FALLBACK_FREE_MODELS if m != model]
    else:
        models_to_try = [model]

    last_err: Optional[Exception] = None

    for attempt_model in models_to_try:
        kwargs: Dict[str, Any] = {
            "model": attempt_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 8192,
        }

        # Only include tools if enabled
        if enable_tools:
            try:
                kwargs["tools"] = MCP_FUNCTION_TOOLS
                kwargs["tool_choice"] = "auto"
            except Exception:
                pass

        try:
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            content = choice.message.content or ""
            tool_calls = []

            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments) if tc.function.arguments else {},
                    })

            return content, tool_calls, attempt_model

        except Exception as e:
            err_str = str(e).lower()
            last_err = e

            # If tool calling fails on certain free models, retry this model once without tools
            if enable_tools and "tools" in err_str:
                try:
                    kwargs.pop("tools", None)
                    kwargs.pop("tool_choice", None)
                    response = client.chat.completions.create(**kwargs)
                    choice = response.choices[0]
                    content = choice.message.content or ""
                    return content, [], attempt_model
                except Exception as inner_e:
                    last_err = inner_e
                    err_str = str(inner_e).lower()

            # If 429 rate limit or model unavailable, continue to next fallback candidate
            if any(code in err_str for code in ["429", "rate limit", "rate-limited", "404", "unavailable", "503", "overloaded"]):
                logger.warning(f"Model {attempt_model} rate-limited or unavailable: {e}. Trying fallback...")
                continue
            else:
                # Other non-retryable errors
                raise e

    if last_err:
        raise last_err
    raise RuntimeError("Failed to call LLM API.")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Session State Initialization
# ─────────────────────────────────────────────────────────────────────────────

if "generated_resume" not in st.session_state:
    st.session_state.generated_resume = ""
if "job_description_text" not in st.session_state:
    st.session_state.job_description_text = ""
if "candidate_bio_text" not in st.session_state:
    st.session_state.candidate_bio_text = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {
            "role": "assistant",
            "content": "👋 **Welcome to ResumeForge ATS Studio!**\n\nUpload your target **Job Description** and candidate profile, then click **⚡ Generate ATS Resume** to build your tailored resume with OpenRouter AI and MCP tools.\n\nYou can also chat with me here anytime to refine sections, add missing keywords, or optimize for specific roles!",
        }
    ]
if "ats_metrics" not in st.session_state:
    st.session_state.ats_metrics = None
if "last_model_used" not in st.session_state:
    st.session_state.last_model_used = None
if "selected_model_requested" not in st.session_state:
    st.session_state.selected_model_requested = None


# ─────────────────────────────────────────────────────────────────────────────
# 7. Sidebar Configuration
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚡ ResumeForge Settings")
    st.markdown('<span class="mcp-pill">🔌 MCP Server Integrated</span>', unsafe_allow_html=True)
    st.markdown("---")

    # Provider Selection
    provider = st.selectbox(
        "AI Provider:",
        ["OpenRouter (Recommended — 20k+ Token Limits)", "Groq", "Custom OpenAI-Compatible"],
        index=0,
    )

    if provider == "OpenRouter (Recommended — 20k+ Token Limits)":
        base_url = "https://openrouter.ai/api/v1"
        env_key = os.getenv("OPENROUTER_API_KEY", "") or os.getenv("OPEN_ROUTER_API_KEY", "")
        api_key = st.text_input(
            "OpenRouter API Key",
            value=env_key,
            type="password",
            help="Enter your OpenRouter API Key (starts with sk-or-...). You can also set OPENROUTER_API_KEY in your .env file.",
        )
        
        model_family = st.radio(
            "Filter by Provider / Family:",
            ["All Free Models", "🔵 Google", "🟠 Meta Llama", "🟣 Qwen & Mistral", "🧠 NVIDIA Nemotron", "💻 Cohere & Others", "Paid / Official"],
            index=0,
            horizontal=False,
        )

        all_models_dict = {m[0]: m[1] for m in OPENROUTER_DEFAULT_MODELS}

        if model_family == "🔵 Google":
            filtered_ids = [m[0] for m in OPENROUTER_DEFAULT_MODELS if "google/" in m[0]]
        elif model_family == "🟠 Meta Llama":
            filtered_ids = [m[0] for m in OPENROUTER_DEFAULT_MODELS if "meta-llama/" in m[0] and ":free" in m[0]]
        elif model_family == "🟣 Qwen & Mistral":
            filtered_ids = [m[0] for m in OPENROUTER_DEFAULT_MODELS if ("qwen/" in m[0] or "mistralai/" in m[0]) and ":free" in m[0]]
        elif model_family == "🧠 NVIDIA Nemotron":
            filtered_ids = [m[0] for m in OPENROUTER_DEFAULT_MODELS if "nvidia/" in m[0]]
        elif model_family == "💻 Cohere & Others":
            filtered_ids = [m[0] for m in OPENROUTER_DEFAULT_MODELS if any(k in m[0] for k in ["cohere/", "poolside/", "z-ai/", "dots-studio/", "openai/gpt-oss", "liquid/", "stealth/", "openrouter/free"])]
        elif model_family == "Paid / Official":
            filtered_ids = [m[0] for m in OPENROUTER_DEFAULT_MODELS if not (":free" in m[0] or "preview" in m[0] or "stealth" in m[0])]
        else:
            # All Free Models
            filtered_ids = [m[0] for m in OPENROUTER_DEFAULT_MODELS if (":free" in m[0] or "preview" in m[0] or "stealth" in m[0] or "openrouter/free" in m[0])]

        selected_model_preset = st.selectbox(
            "Select Free Model:",
            options=filtered_ids + ["Custom Model ID..."],
            format_func=lambda x: all_models_dict.get(x, x),
            index=0,
        )
        if selected_model_preset == "Custom Model ID...":
            selected_model = st.text_input("Enter Model ID (e.g. google/gemma-4-31b-it:free):", "google/gemma-4-31b-it:free")
        else:
            selected_model = selected_model_preset

    elif provider == "Groq":
        base_url = "https://api.groq.com/openai/v1"
        env_key = os.getenv("GROQ_API_KEY", "")
        api_key = st.text_input("Groq API Key", value=env_key, type="password")
        selected_model = st.selectbox(
            "Groq Model:",
            ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "deepseek-r1-distill-llama-70b", "mixtral-8x7b-32768"],
            index=0,
        )

    else:
        base_url = st.text_input("Custom Base URL", value="https://openrouter.ai/api/v1")
        api_key = st.text_input("API Key", type="password")
        selected_model = st.text_input("Model Name", value="deepseek/deepseek-r1:free")

    temperature = st.slider(
        "Creativity / Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.15,
        step=0.05,
        help="Lower values (0.1 - 0.2) produce highly factual, strict ATS resumes.",
    )

    st.markdown("---")
    st.markdown("### 🎯 Context & Token Mode")

    context_mode = st.radio(
        "Candidate Biography Depth:",
        ["⚡ Smart ATS Optimized (~4k tokens)", "🎯 Balanced (~8k tokens)", "📚 Full 60-File Dump (20k+ tokens)"],
        index=0,
        help="Smart mode automatically selects the most relevant projects matching your JD. Full mode includes all 60 source files.",
    )
    mode_key = "smart" if "Smart" in context_mode else ("balanced" if "Balanced" in context_mode else "full")

    st.markdown("---")
    st.markdown("### 📂 Candidate Data Source")

    bio_source_mode = st.radio(
        "Source for Candidate Profile:",
        ["Use Repository md/ Data", "Upload Custom Files / Resumes"],
        index=0,
    )

    raw_repo_files = load_repository_md_files()
    if bio_source_mode == "Use Repository md/ Data":
        if raw_repo_files:
            st.success(f"✅ Found {len(raw_repo_files)} source files in `md/`")
            bio_text, est_tok = build_smart_biography(
                raw_repo_files,
                st.session_state.job_description_text,
                mode=mode_key,
            )
            st.session_state.candidate_bio_text = bio_text
            st.markdown(f'<span class="token-pill">📊 Context Payload: ~{est_tok:,} tokens</span>', unsafe_allow_html=True)
            
            with st.expander("🔍 View Detected Biography Files", expanded=False):
                for f_name in raw_repo_files.keys():
                    st.caption(f"• `{f_name}`")
        else:
            st.warning("⚠️ No files found in repository `md/`. Please switch to Upload mode.")
            st.session_state.candidate_bio_text = ""
    else:
        uploaded_candidate_files = st.file_uploader(
            "Upload Resumes, Bio, or Exports",
            type=["pdf", "docx", "txt", "md", "zip"],
            accept_multiple_files=True,
            help="Upload your past resumes, markdown notes, or zip export archives.",
        )
        if uploaded_candidate_files:
            custom_bio_parts = []
            for u_file in uploaded_candidate_files:
                f_bytes = u_file.read()
                if u_file.name.endswith(".zip"):
                    zip_extracted = extract_files_from_zip(f_bytes)
                    for z_name, z_content in zip_extracted.items():
                        custom_bio_parts.append(f"══════ FILE: {z_name} ══════\n{z_content}")
                else:
                    text_extracted = extract_text_from_file_bytes(u_file.name, f_bytes)
                    if text_extracted:
                        custom_bio_parts.append(f"══════ FILE: {u_file.name} ══════\n{text_extracted}")
            
            st.session_state.candidate_bio_text = "\n\n".join(custom_bio_parts)
            est_tok = len(st.session_state.candidate_bio_text) // 4
            st.info(f"Loaded {len(uploaded_candidate_files)} file(s) (~{est_tok:,} tokens)")

    st.markdown("---")
    st.caption("Powered by **OpenRouter** & **ResumeForge MCP Server**")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Main Application Interface
# ─────────────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-header">ResumeForge ATS Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Generate ultra-high ATS scoring resumes tailored to any Job Description with OpenRouter AI & ResumeForge MCP tools.</div>',
    unsafe_allow_html=True,
)

col_left, col_right = st.columns([1.1, 1.3], gap="large")

# ───────────────────────────────────────────
# Left Column: Upload & Generation Panel
# ───────────────────────────────────────────
with col_left:
    st.markdown("### 1. Job Description & Input")

    uploaded_jd = st.file_uploader(
        "📄 Drag & Drop Target Job Description (PDF, DOCX, TXT, MD)",
        type=["txt", "md", "pdf", "docx"],
        help="Upload the official job description file to extract requirements & keywords.",
    )

    jd_file_text = ""
    if uploaded_jd is not None:
        jd_file_text = extract_text_from_file_bytes(uploaded_jd.name, uploaded_jd.read())
        if jd_file_text:
            st.success(f"✅ Loaded `{uploaded_jd.name}` ({len(jd_file_text)} characters)")

    jd_input = st.text_area(
        "Or Paste Job Description Text Directly:",
        value=jd_file_text if jd_file_text else st.session_state.job_description_text,
        height=200,
        placeholder="Paste the complete job description, requirements, responsibilities, and company details here...",
    )
    st.session_state.job_description_text = jd_input

    # Recalculate smart biography if JD text updated
    if bio_source_mode == "Use Repository md/ Data" and raw_repo_files:
        st.session_state.candidate_bio_text, _ = build_smart_biography(
            raw_repo_files,
            st.session_state.job_description_text,
            mode=mode_key,
        )

    # Generation Button & MCP Action
    st.markdown("### 2. Tailor & Generate")
    generate_btn = st.button("⚡ Generate ATS-Optimized Resume", type="primary", use_container_width=True)

    if generate_btn:
        if not api_key:
            st.error("❌ Please provide a valid **API Key** in the sidebar to generate.")
        elif not st.session_state.job_description_text.strip():
            st.error("❌ Please upload or paste a **Job Description**.")
        elif not st.session_state.candidate_bio_text.strip():
            st.error("❌ No candidate biography data available. Please check `md/` or upload candidate files.")
        else:
            with st.spinner(f"🚀 Generating ATS Resume via {selected_model} & MCP Tools..."):
                try:
                    biography_content = st.session_state.candidate_bio_text
                    target_jd = st.session_state.job_description_text

                    user_prompt = f"""
Please generate the tailored, 95%+ ATS-optimized Markdown resume for the following candidate and target job description.

CRITICAL INSTRUCTION: The resume MUST fit strictly onto ONE single physical page. Select the top 2-3 most relevant experiences and at most 4 projects (top 2 to 4 projects). Write punchy, quantified, high-impact bullet points.

DO NOT write drafting notes, count words, or explain your process. Output ONLY the raw final Markdown resume starting immediately with '# VIJAYAKANTH M'.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CANDIDATE BIOGRAPHY DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{biography_content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET JOB DESCRIPTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{target_jd}
""".strip()

                    messages = [
                        {"role": "system", "content": HIGH_POWERED_ATS_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ]

                    generated_text, tool_calls, model_used = call_llm_api(
                        api_key=api_key,
                        model=selected_model,
                        messages=messages,
                        temperature=temperature,
                        enable_tools=False,
                        base_url=base_url,
                    )

                    clean_resume = extract_clean_single_resume(generated_text)
                    if not clean_resume:
                        clean_resume = generated_text.strip()

                    st.session_state.generated_resume = clean_resume
                    st.session_state.ats_metrics = calculate_ats_metrics(clean_resume, target_jd)
                    st.session_state.last_model_used = model_used
                    st.session_state.selected_model_requested = selected_model

                    try:
                        out_dir = PROJECT_ROOT / "md" / "tailored"
                        out_dir.mkdir(parents=True, exist_ok=True)
                        save_path = out_dir / "Tailored_Resume.md"
                        save_path.write_text(clean_resume, encoding="utf-8")
                    except Exception:
                        pass

                    model_note = f"using **{model_used}**"
                    if model_used != selected_model:
                        model_note = f"using backup **{model_used}** (auto-routed because **{selected_model}** was temporarily busy upstream)"

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": f"✨ **Tailored ATS Resume Generated!** (ATS Score: **{st.session_state.ats_metrics['score']}%**)\n\nMatched **{st.session_state.ats_metrics['matched_count']} keywords** from the Job Description {model_note}. Review the preview on the right or chat with me to adjust any section!",
                    })

                    st.toast("🎉 Resume generated and optimized for ATS!", icon="⚡")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error generating resume: {e}")
                    logger.exception("LLM Generation Error")


# ───────────────────────────────────────────
# Right Column: Output Dashboard & Preview
# ───────────────────────────────────────────
with col_right:
    st.markdown("### 3. ATS Studio & Results")

    # Display Active Model Attribution Badge
    if st.session_state.last_model_used:
        actual_model = st.session_state.last_model_used
        requested_model = st.session_state.get("selected_model_requested", actual_model)
        is_failover = (actual_model != requested_model)

        if is_failover:
            st.markdown(
                f"""
                <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.4); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <span style="font-size: 0.72rem; color: #fbbf24; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Generated by Backup Model</span>
                        <div style="font-size: 0.92rem; font-weight: 600; color: #fef08a; margin-top: 1px;">
                            🤖 <code>{actual_model}</code>
                        </div>
                    </div>
                    <span style="background: rgba(245, 158, 11, 0.25); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.5); border-radius: 6px; padding: 3px 8px; font-size: 0.72rem; font-weight: 600;">
                        ⚡ Auto-failover from {requested_model}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.35); border-radius: 8px; padding: 8px 12px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <span style="font-size: 0.72rem; color: #a5b4fc; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Generated by AI Model:</span>
                        <div style="font-size: 0.92rem; font-weight: 600; color: #e0e7ff; margin-top: 1px;">
                            🤖 <code>{actual_model}</code>
                        </div>
                    </div>
                    <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 6px; padding: 3px 8px; font-size: 0.72rem; font-weight: 600;">
                        ✓ Model Match
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    tab_preview, tab_metrics, tab_editor = st.tabs([
        "📄 Rendered Resume",
        "📊 ATS Score & Match",
        "📝 Markdown Editor",
    ])

    # Tab 1: Rendered Resume Preview
    with tab_preview:
        if st.session_state.generated_resume:
            col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
            with col_save1:
                st.download_button(
                    label="💾 Download Markdown",
                    data=st.session_state.generated_resume,
                    file_name="ATS_Tailored_Resume.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with col_save2:
                if st.button("📁 Save to md/tailored/", use_container_width=True):
                    try:
                        out_dir = PROJECT_ROOT / "md" / "tailored"
                        out_dir.mkdir(parents=True, exist_ok=True)
                        target_file = out_dir / "Tailored_Resume.md"
                        target_file.write_text(st.session_state.generated_resume, encoding="utf-8")
                        st.success(f"Saved to `{target_file.relative_to(PROJECT_ROOT)}`")
                    except Exception as err:
                        st.error(f"Could not save: {err}")
            with col_save3:
                if st.button("📋 Copy Resume Text", use_container_width=True):
                    st.toast("Resume text ready to copy from the editor tab!", icon="📋")

            st.markdown("---")
            st.markdown(f'<div class="resume-preview-box">{st.session_state.generated_resume}</div>', unsafe_allow_html=True)
        else:
            st.info("💡 Upload your Job Description and click **⚡ Generate ATS-Optimized Resume** to view the preview here.")

    # Tab 2: ATS Score & Analytics
    with tab_metrics:
        if st.session_state.ats_metrics:
            metrics = st.session_state.ats_metrics
            score = metrics["score"]

            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                score_color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 60 else "#ef4444")
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div style="color: #94a3b8; font-size: 0.85rem; font-weight:600;">ATS MATCH SCORE</div>
                        <div class="metric-val" style="color: {score_color};">{score}%</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">Compatibility Rating</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_m2:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div style="color: #94a3b8; font-size: 0.85rem; font-weight:600;">MATCHED KEYWORDS</div>
                        <div class="metric-val" style="color: #34d399;">{metrics['matched_count']}</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">Found in Resume</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_m3:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div style="color: #94a3b8; font-size: 0.85rem; font-weight:600;">MISSING KEYWORDS</div>
                        <div class="metric-val" style="color: #f87171;">{metrics['missing_count']}</div>
                        <div style="font-size: 0.75rem; color: #94a3b8;">Suggestions to Add</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown("#### ✅ Matched Target Keywords")
            matched_badges = "".join([f'<span class="badge badge-green">{kw}</span>' for kw in metrics["matched"]])
            st.markdown(matched_badges or "_No matching keywords identified_", unsafe_allow_html=True)

            st.markdown("#### ⚠️ Missing / Recommended Keywords from JD")
            missing_badges = "".join([f'<span class="badge badge-red">{kw}</span>' for kw in metrics["missing"]])
            st.markdown(missing_badges or "_All key JD terms are covered!_", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("💡 **Pro-Tip for 95%+ ATS Score:** Use the AI Chatbot below and click **'🎯 Add Missing Keywords'** to automatically infuse the missing competencies into your projects and skills!")
        else:
            st.info("📊 Generate a resume to compute real-time ATS match analytics and keyword breakdown.")

    # Tab 3: Markdown Editor
    with tab_editor:
        edited_resume = st.text_area(
            "Live Markdown Editor",
            value=st.session_state.generated_resume,
            height=500,
            help="You can manually edit any section of the Markdown resume here.",
        )
        if edited_resume != st.session_state.generated_resume:
            st.session_state.generated_resume = edited_resume
            if st.session_state.job_description_text:
                st.session_state.ats_metrics = calculate_ats_metrics(edited_resume, st.session_state.job_description_text)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Interactive AI Resume Chatbot
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### 💬 Conversational Resume AI Assistant")
st.caption("Ask questions, request section rewrites, inject missing keywords, or optimize for specific interview criteria.")

# Quick Action Suggestions
quick_cols = st.columns(5)
with quick_cols[0]:
    if st.button("🚀 Boost ATS Score", use_container_width=True):
        st.session_state.quick_action_prompt = "Please rewrite the resume to maximize the ATS match score, ensuring all critical keywords from the Job Description are woven naturally into the Skills and Experience sections."
with quick_cols[1]:
    if st.button("🎯 Add Missing Keywords", use_container_width=True):
        st.session_state.quick_action_prompt = "Review the missing keywords from the ATS analysis and integrate any that the candidate has legitimate background in into the Skills and Projects sections."
with quick_cols[2]:
    if st.button("📈 Quantify Metrics", use_container_width=True):
        st.session_state.quick_action_prompt = "Enhance the bullet points in the Experience and Projects sections using Google's X-Y-Z formula with quantified metrics, percentages, and tangible business impact."
with quick_cols[3]:
    if st.button("💼 Senior / Lead Tone", use_container_width=True):
        st.session_state.quick_action_prompt = "Adjust the summary, leadership emphasis, and architecture language to position the candidate strongly for a Senior / Lead Engineering role."
with quick_cols[4]:
    if st.button("📄 Fit 1-Page Layout", use_container_width=True):
        st.session_state.quick_action_prompt = "Condense the resume into a concise, high-density 1-page layout without sacrificing core ATS keywords or major accomplishments."

# Render Chat History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input Handler
prompt_to_send = None
if "quick_action_prompt" in st.session_state and st.session_state.quick_action_prompt:
    prompt_to_send = st.session_state.quick_action_prompt
    st.session_state.quick_action_prompt = None

chat_input = st.chat_input("Type your message or request to the AI assistant...")
if chat_input:
    prompt_to_send = chat_input

if prompt_to_send:
    if not api_key:
        st.error("Please enter an API Key in the sidebar.")
    else:
        st.session_state.chat_history.append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user"):
            st.markdown(prompt_to_send)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    convo_messages = [
                        {
                            "role": "system",
                            "content": (
                                f"{HIGH_POWERED_ATS_SYSTEM_PROMPT}\n\n"
                                "You are assisting the user interactively. When providing an updated resume, output the full or modified Markdown resume clearly. "
                                f"Current Target Job Description:\n{st.session_state.job_description_text[:1500]}\n\n"
                                f"Current Active Resume Markdown:\n{st.session_state.generated_resume[:2500]}"
                            ),
                        }
                    ]

                    for m in st.session_state.chat_history[-6:]:
                        convo_messages.append({"role": m["role"], "content": m["content"]})

                    response_text, tool_calls, model_used = call_llm_api(
                        api_key=api_key,
                        model=selected_model,
                        messages=convo_messages,
                        temperature=temperature,
                        enable_tools=True,
                        base_url=base_url,
                    )

                    if tool_calls:
                        for tc in tool_calls:
                            tool_result = execute_mcp_tool_locally(
                                tc["name"],
                                tc["arguments"],
                                st.session_state.candidate_bio_text,
                            )
                            convo_messages.append({
                                "role": "function",
                                "name": tc["name"],
                                "content": tool_result,
                            })
                        response_text, _, model_used = call_llm_api(
                            api_key=api_key,
                            model=selected_model,
                            messages=convo_messages,
                            temperature=temperature,
                            enable_tools=False,
                            base_url=base_url,
                        )

                    st.markdown(response_text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response_text})

                    if "## Professional Summary" in response_text or "## Skills" in response_text:
                        clean_candidate_resume = extract_clean_single_resume(response_text)
                        if len(clean_candidate_resume) > 200:
                            st.session_state.generated_resume = clean_candidate_resume
                            if st.session_state.job_description_text:
                                st.session_state.ats_metrics = calculate_ats_metrics(
                                    clean_candidate_resume, st.session_state.job_description_text
                                )
                            st.rerun()

                except Exception as e:
                    err_msg = f"❌ Error communicating with {provider}: {e}"
                    st.error(err_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": err_msg})
