"""Thread-safe SQLite database manager with backup and versioning for ATS Benchmark."""
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import settings
from database.migrations import init_db
from database.models import ComparisonRecord


class DatabaseManager:
    """Manages SQLite operations, active version tracking, and timestamped backups."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def get_connection(self) -> sqlite3.Connection:
        """Opens a SQLite connection with row factory enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Runs initialization script to create tables and indices."""
        with self.get_connection() as conn:
            init_db(conn)

    def backup_database(self, label: str = "manual") -> Path:
        """Creates a timestamped snapshot of the SQLite database."""
        backup_dir = settings.backup_dir
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"ats_benchmark_{label}_{timestamp}.db"
        shutil.copy2(self.db_path, backup_file)
        return backup_file

    def get_next_comparison_id(self) -> str:
        """Determines the next sequential comparison ID (e.g. C001, C002, ...)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT comparison_id FROM comparisons WHERE is_active = 1")
            rows = cursor.fetchall()
            if not rows:
                return "C001"
            
            existing_nums = []
            for r in rows:
                cid = str(r["comparison_id"]).strip()
                if cid.startswith("C") and cid[1:].isdigit():
                    existing_nums.append(int(cid[1:]))
            
            if not existing_nums:
                return f"C{len(rows) + 1:03d}"
            
            next_num = max(existing_nums) + 1
            return f"C{next_num:03d}"

    def save_comparison(self, rec: ComparisonRecord) -> int:
        """
        Saves a comparison record. If an active record exists for (model, jd),
        deactivates the old version and inserts the new version.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find latest version for (model, jd)
            cursor.execute(
                "SELECT version FROM comparisons WHERE model = ? AND jd = ? ORDER BY version DESC LIMIT 1",
                (rec.model, rec.jd),
            )
            row = cursor.fetchone()
            
            if row:
                next_version = row["version"] + 1
                cursor.execute(
                    "UPDATE comparisons SET is_active = 0 WHERE model = ? AND jd = ?",
                    (rec.model, rec.jd),
                )
            else:
                next_version = 1
            
            rec.version = next_version
            rec.is_active = True
            rec.updated_at = datetime.utcnow().isoformat()
            
            insert_sql = """
            INSERT INTO comparisons (
                comparison_id, model, jd, version, is_active,
                ai_status, ai_overall_reported, ai_overall_calculated,
                ai_keyword_match, ai_skills_coverage, ai_ats_formatting,
                ai_role_alignment, ai_impact_metrics,
                human_status, human_overall_reported, human_overall_calculated,
                human_keyword_match, human_skills_coverage, human_ats_formatting,
                human_role_alignment, human_impact_metrics,
                reported_ats_advantage, calculated_ats_advantage, relative_increase_percent,
                winner, ai_strengths, ai_weaknesses, human_strengths, human_weaknesses, winner_reasons,
                claude_chat_url, raw_report_text, is_math_consistent, notes, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
            """
            cursor.execute(
                insert_sql,
                (
                    rec.comparison_id, rec.model, rec.jd, rec.version, 1 if rec.is_active else 0,
                    rec.ai_status, rec.ai_overall_reported, rec.ai_overall_calculated,
                    rec.ai_keyword_match, rec.ai_skills_coverage, rec.ai_ats_formatting,
                    rec.ai_role_alignment, rec.ai_impact_metrics,
                    rec.human_status, rec.human_overall_reported, rec.human_overall_calculated,
                    rec.human_keyword_match, rec.human_skills_coverage, rec.human_ats_formatting,
                    rec.human_role_alignment, rec.human_impact_metrics,
                    rec.reported_ats_advantage, rec.calculated_ats_advantage, rec.relative_increase_percent,
                    rec.winner, rec.ai_strengths, rec.ai_weaknesses, rec.human_strengths, rec.human_weaknesses, rec.winner_reasons,
                    rec.claude_chat_url, rec.raw_report_text, 1 if rec.is_math_consistent else 0, rec.notes, rec.created_at, rec.updated_at
                ),
            )
            record_id = cursor.lastrowid
            conn.commit()
            return record_id

    def get_comparison(self, comparison_id: str) -> Optional[Dict[str, Any]]:
        """Fetches active record for comparison_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comparisons WHERE comparison_id = ? AND is_active = 1", (comparison_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_comparison_by_model_jd(self, model: str, jd: str) -> Optional[Dict[str, Any]]:
        """Fetches active record for model and JD."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comparisons WHERE model = ? AND jd = ? AND is_active = 1", (model, jd))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_active_comparisons(self) -> List[Dict[str, Any]]:
        """Fetches all active comparison records ordered by comparison_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comparisons WHERE is_active = 1 ORDER BY comparison_id ASC")
            return [dict(r) for r in cursor.fetchall()]

    def delete_comparison(self, comparison_id: str):
        """Soft deletes an active comparison."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE comparisons SET is_active = 0 WHERE comparison_id = ?", (comparison_id,))
            conn.commit()


db = DatabaseManager()
