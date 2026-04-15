"""Search functions for the 4 compliance FTS5 collections."""
from app.core.database import get_connection
from app.core.config import COMPLIANCE_PAGE_SIZE


def _rows_to_dicts(rows):
    return [dict(r) for r in rows]


def search_penalties(query: str, page: int = 1):
    """Full-text search against compliance_penalties.
    Returns (list[dict], total_count).
    """
    if len(query) < 2:
        return [], 0
    offset = (page - 1) * COMPLIANCE_PAGE_SIZE
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM compliance_penalties_fts"
            " WHERE compliance_penalties_fts MATCH ?",
            (query,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT p.id, p.category, p.institution, p.title, p.issued_date, p.content"
            " FROM compliance_penalties_fts fts"
            " JOIN compliance_penalties p ON p.id = fts.rowid"
            " WHERE compliance_penalties_fts MATCH ?"
            " ORDER BY p.issued_date DESC"
            " LIMIT ? OFFSET ?",
            (query, COMPLIANCE_PAGE_SIZE, offset)
        ).fetchall()
    return _rows_to_dicts(rows), total


def search_regulations(query: str, page: int = 1):
    """Full-text search against compliance_regulations.
    Returns (list[dict], total_count).
    """
    if len(query) < 2:
        return [], 0
    offset = (page - 1) * COMPLIANCE_PAGE_SIZE
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM compliance_regulations_fts"
            " WHERE compliance_regulations_fts MATCH ?",
            (query,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT r.id, r.category, r.title, r.issued_date, r.content"
            " FROM compliance_regulations_fts fts"
            " JOIN compliance_regulations r ON r.id = fts.rowid"
            " WHERE compliance_regulations_fts MATCH ?"
            " ORDER BY r.issued_date DESC"
            " LIMIT ? OFFSET ?",
            (query, COMPLIANCE_PAGE_SIZE, offset)
        ).fetchall()
    return _rows_to_dicts(rows), total


def search_national_laws(query: str, page: int = 1):
    """Full-text search against compliance_national_laws.
    Returns (list[dict], total_count).
    """
    if len(query) < 2:
        return [], 0
    offset = (page - 1) * COMPLIANCE_PAGE_SIZE
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM compliance_national_laws_fts"
            " WHERE compliance_national_laws_fts MATCH ?",
            (query,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT n.id, n.law_name, n.law_level, n.law_url, n.article_no, n.article_content"
            " FROM compliance_national_laws_fts fts"
            " JOIN compliance_national_laws n ON n.id = fts.rowid"
            " WHERE compliance_national_laws_fts MATCH ?"
            " ORDER BY n.law_name, n.id"
            " LIMIT ? OFFSET ?",
            (query, COMPLIANCE_PAGE_SIZE, offset)
        ).fetchall()
    return _rows_to_dicts(rows), total


def search_fsc_regs(query: str, page: int = 1):
    """Full-text search against compliance_fsc_regs.
    Returns (list[dict], total_count).
    """
    if len(query) < 2:
        return [], 0
    offset = (page - 1) * COMPLIANCE_PAGE_SIZE
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM compliance_fsc_regs_fts"
            " WHERE compliance_fsc_regs_fts MATCH ?",
            (query,)
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT f.id, f.institution, f.reg_category, f.reg_name, f.purpose,"
            "       f.effective_date, f.amendment_date, f.change_type, f.content"
            " FROM compliance_fsc_regs_fts fts"
            " JOIN compliance_fsc_regs f ON f.id = fts.rowid"
            " WHERE compliance_fsc_regs_fts MATCH ?"
            " ORDER BY f.effective_date DESC"
            " LIMIT ? OFFSET ?",
            (query, COMPLIANCE_PAGE_SIZE, offset)
        ).fetchall()
    return _rows_to_dicts(rows), total
