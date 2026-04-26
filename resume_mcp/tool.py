"""
Resume History MCP Tool — Gateway
====================================
Single entry point: scan a folder of resume files (PDF/DOCX),
extract, deduplicate, build timeline, and produce a clean Markdown
career profile.

Usage:
    # Reads RESUME_HISTORY_PATH from .env
    resume_history_analyze()

    # Or pass path directly
    resume_history_analyze(folder_path="/path/to/resumes")

Pipeline:
    1. Discover & order files (oldest → newest by mtime)
    2. Extract each file  (pdfplumber → PyMuPDF → docx)
    3. Classify each file (generic | company_specific)
    4. Aggregate all data into ResumeHistory
    5. Deduplicate (fuzzy for projects/jobs, exact for skills/certs)
    6. Build career timeline
    7. Write md/resume/resume_history.md
"""

from __future__ import annotations

import logging
from pathlib import Path

from .aggregator import aggregate
from .classifier import classify
from .config import DEFAULT_OUTPUT_DIR, SUPPORTED_EXTENSIONS
from .deduplicator import deduplicate
from .exceptions import (
    ExtractionError,
    FolderNotFoundError,
    MarkdownWriteError,
    NoResumesFoundError,
    ResumeMCPError,
)
from .extractor import extract
from .markdown_writer import write_resume_history
from .schemas import AnalysisResult, RawResume
from .timeline import build_timeline

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# MCP Gateway Tool
# ──────────────────────────────────────────────────────────────────────


def resume_history_analyze(
    folder_path: str | None = None,
    output_dir: str | None = None,
) -> dict:
    """
    Analyze a folder of resume files, extract the raw data, and prompt
    the calling LLM to deduplicate and structure it into a Markdown file.

    Args:
        folder_path: Path to folder containing PDF/DOCX resumes.
                     If not provided, reads RESUME_HISTORY_PATH from .env.
        output_dir:  Custom output directory. Defaults to md/resume/
                     in the project root.

    Returns:
        A dict with the following keys:
          - ``success`` (bool): ``True`` if the pipeline completed successfully.
          - ``prompt`` (str): The formatted prompt for the calling LLM (on success).
          - ``files_processed`` (list[str]): Names of files successfully processed.
          - ``files_failed`` (list[str]): Names of files that failed extraction.
          - ``errors`` (list[str]): Error messages (populated on failure).
    """
    result = AnalysisResult()

    try:
        # ── Step 0: Resolve folder path ──────────────────────────────
        if not folder_path:
            from env_loader import get_env
            folder_path = get_env("RESUME_HISTORY_PATH")

        if not folder_path:
            raise FolderNotFoundError(
                "No folder_path provided and RESUME_HISTORY_PATH not set in .env"
            )

        folder = Path(folder_path)
        if not folder.exists():
            raise FolderNotFoundError(f"Folder does not exist: {folder}")
        if not folder.is_dir():
            raise FolderNotFoundError(f"Path is not a folder: {folder}")

        # ── Step 1: Discover files ────────────────────────────────────
        files = _discover_files(folder)
        if not files:
            raise NoResumesFoundError(
                f"No supported resume files found in '{folder}'",
                details=f"Supported types: {', '.join(SUPPORTED_EXTENSIONS)}",
            )

        logger.info("Discovered %d resume file(s) in '%s'", len(files), folder)

        # ── Step 2 & 3: Extract + Classify each file ─────────────────
        resumes: list[RawResume] = []
        for file in files:
            try:
                raw = extract(file)
                classify(raw)
                resumes.append(raw)
                result.files_processed.append(file.name)
                logger.info("Processed: %s (type=%s)", file.name, raw.resume_type)
            except ExtractionError as e:
                result.files_failed.append(file.name)
                result.errors.append(str(e))
                logger.warning("Skipped '%s': %s", file.name, e)

        if not resumes:
            raise NoResumesFoundError(
                "All resume files failed extraction",
                details="Check extraction_warnings in output for details",
            )

        # ── Step 4: Aggregate ─────────────────────────────────────────
        history = aggregate(resumes)

        # ── Step 5: Deduplicate ───────────────────────────────────────
        history = deduplicate(history)

        # ── Step 6: Timeline ──────────────────────────────────────────
        history = build_timeline(resumes, history)

        # ── Step 7: Hand off to the client LLM ────────────────────────────
        # Instead of writing chaotic heuristic markdown, we ask the calling LLM
        # to format it beautifully.
        out_path = (
            Path(output_dir)
            if output_dir
            else Path(__file__).resolve().parent.parent / DEFAULT_OUTPUT_DIR
        )
        
        # Prepare the raw text for the LLM
        raw_payload = []
        raw_payload.append(f"Identity: {history.identity}")
        for exp in history.experiences:
            raw_payload.append(f"Experience Entry: {exp.get('raw', exp)}")
        for proj in history.projects:
            raw_payload.append(f"Project Entry: {proj.get('raw', proj)}")
        raw_payload.append(f"Skills: {history.skills}")
        for edu in history.education:
            raw_payload.append(f"Education Entry: {edu.get('raw', edu)}")
        raw_payload.append(f"Certs: {history.certifications}")
        for sec in history.raw_sections_unclassified:
            raw_payload.append(f"Unclassified Section [{sec.heading}]: {sec.content}")
            
        full_raw_text = "\n\n".join(raw_payload)

        prompt = f"""
I have successfully extracted the raw, unstructured data from {len(result.files_processed)} resume files.
Because PDF extraction is messy, the raw text below is chaotic. 

**YOUR TASK AS THE AI:**
1. Read the raw data below.
2. Deduplicate roles, projects, and skills.
3. Chronologically order the experiences and projects.
4. Format everything into a PERFECT, professional Markdown resume.
5. You MUST save the final Markdown to the following file path using your file-writing capabilities:
   {out_path / "resume_history.md"}
6. If you cannot write to files natively, output the Markdown here in our chat.

RAW DATA:
================
{full_raw_text}
"""
        return {
            "success": True,
            "prompt": prompt,
            "files_processed": result.files_processed,
            "files_failed": result.files_failed,
            "errors": result.errors,
        }

    except (FolderNotFoundError, NoResumesFoundError) as e:
        result.errors.append(f"Input error: {e}")
        return {
            "success": False,
            "errors": result.errors,
            "files_processed": result.files_processed,
            "files_failed": result.files_failed,
        }
    except ResumeMCPError as e:
        result.errors.append(f"Pipeline error: {e}")
        return {
            "success": False,
            "errors": result.errors,
            "files_processed": result.files_processed,
            "files_failed": result.files_failed,
        }
    except Exception as e:
        result.errors.append(f"Unexpected error in resume_history_analyze: {e}")
        return {
            "success": False,
            "errors": result.errors,
            "files_processed": result.files_processed,
            "files_failed": result.files_failed,
        }


# ──────────────────────────────────────────────────────────────────────
# File Discovery
# ──────────────────────────────────────────────────────────────────────


def _discover_files(folder: Path) -> list[Path]:
    """
    Find all supported resume files in a folder (non-recursive).
    Sorted oldest → newest by last modified time.
    Temp/hidden files are excluded.
    """
    files: list[Path] = []
    for f in folder.iterdir():
        if not f.is_file():
            continue
        if f.name.startswith(".") or f.name.startswith("~"):
            continue  # skip hidden/temp files
        if f.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(f)

    # Sort oldest → newest by mtime (defines career timeline order)
    files.sort(key=lambda f: f.stat().st_mtime)
    return files
