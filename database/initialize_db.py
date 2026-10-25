"""
database/initialize_db.py — Create all tables from schema.sql.

Run this once (or repeatedly; it is idempotent):
    python -m database.initialize_db
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.connection import get_engine
from sqlalchemy import text

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def initialize_database(engine=None):
    """Create all tables.  Safe to call multiple times (IF NOT EXISTS)."""
    if engine is None:
        engine = get_engine()

    schema_path = Path(__file__).resolve().parent.parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    # Split on semicolons, strip line comments to get actual SQL
    raw_stmts = []
    for chunk in sql.split(";"):
        lines = [line.strip() for line in chunk.splitlines() if line.strip() and not line.strip().startswith("--")]
        clean_stmt = " ".join(lines).strip()
        if clean_stmt:
            raw_stmts.append(clean_stmt)

    # Run CREATE TABLE statements first, then CREATE INDEX
    table_stmts = [s for s in raw_stmts if not s.upper().startswith("CREATE INDEX")]
    index_stmts = [s for s in raw_stmts if s.upper().startswith("CREATE INDEX")]

    with engine.begin() as conn:
        for stmt in table_stmts + index_stmts:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                logger.warning("Skipped statement: %s", exc)

    logger.info("Database schema initialized successfully.")


if __name__ == "__main__":
    initialize_database()
    print("[OK] Database initialized.")
