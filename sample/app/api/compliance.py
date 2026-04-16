from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.api.auth import get_current_user
from app.core.database import get_conn

router = APIRouter(tags=["compliance"])
PAGE_SIZE = 10


@router.get("/compliance/search")
def search_compliance(
    q: str = Query(default="", description="Search keyword"),
    type: str = Query("penalties"),
    page: int = Query(1, ge=1),
    category: Optional[str] = Query(default=None),
    institution: Optional[str] = Query(default=None),
    law_system: Optional[str] = Query(default=None),
    law_level: Optional[str] = Query(default=None),
    user=Depends(get_current_user),
):
    conn = get_conn()
    try:
        offset = (page - 1) * PAGE_SIZE
        with conn.cursor() as cur:
            if type == "penalties":
                where_clauses = []
                params = []
                if q:
                    where_clauses.append("MATCH(title, content) AGAINST(%s IN BOOLEAN MODE)")
                    params.append(q)
                if category:
                    where_clauses.append("category = %s")
                    params.append(category)
                if institution:
                    where_clauses.append("institution = %s")
                    params.append(institution)
                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cur.execute(
                    f"SELECT id, category, institution, title, date FROM comp_penalties "
                    f"{where_sql} ORDER BY date DESC LIMIT %s OFFSET %s",
                    params + [PAGE_SIZE, offset],
                )
                rows = [{"id": r["id"], "col1": r.get("category",""), "col2": r.get("institution",""), "col3": (r.get("title") or "")[:80], "col4": r.get("date","")} for r in cur.fetchall()]
                headers = ["裁罰類別", "機構", "標題", "日期"]
                cur.execute(
                    f"SELECT COUNT(*) as cnt FROM comp_penalties {where_sql}",
                    params,
                )
                total = cur.fetchone()["cnt"]

            elif type == "regulations":
                where_clauses = []
                params = []
                if q:
                    where_clauses.append("MATCH(title, content) AGAINST(%s IN BOOLEAN MODE)")
                    params.append(q)
                if category:
                    where_clauses.append("category = %s")
                    params.append(category)
                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cur.execute(
                    f"SELECT id, category, title, date FROM comp_regulations "
                    f"{where_sql} ORDER BY date DESC LIMIT %s OFFSET %s",
                    params + [PAGE_SIZE, offset],
                )
                rows = [{"id": r["id"], "col1": r.get("category",""), "col2": (r.get("title") or "")[:80], "col3": r.get("date","")} for r in cur.fetchall()]
                headers = ["類別", "標題", "日期"]
                cur.execute(
                    f"SELECT COUNT(*) as cnt FROM comp_regulations {where_sql}",
                    params,
                )
                total = cur.fetchone()["cnt"]

            elif type == "national":
                where_clauses = []
                params = []
                if q:
                    where_clauses.append("MATCH(law_name, article_content) AGAINST(%s IN BOOLEAN MODE)")
                    params.append(q)
                if law_level:
                    where_clauses.append("law_level = %s")
                    params.append(law_level)
                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cur.execute(
                    f"SELECT id, law_name, article_no, law_level, article_content FROM comp_national_laws "
                    f"{where_sql} LIMIT %s OFFSET %s",
                    params + [PAGE_SIZE, offset],
                )
                rows = [{"id": r["id"], "col1": r.get("law_name",""), "col2": r.get("article_no",""), "col3": r.get("law_level",""), "col4": (r.get("article_content") or "")[:100]} for r in cur.fetchall()]
                headers = ["法規名稱", "條文號", "層級", "條文摘要"]
                cur.execute(
                    f"SELECT COUNT(*) as cnt FROM comp_national_laws {where_sql}",
                    params,
                )
                total = cur.fetchone()["cnt"]

            elif type == "fsc":
                where_clauses = []
                params = []
                if q:
                    where_clauses.append("MATCH(subject, content) AGAINST(%s IN BOOLEAN MODE)")
                    params.append(q)
                if institution:
                    where_clauses.append("institution = %s")
                    params.append(institution)
                if law_system:
                    where_clauses.append("law_system = %s")
                    params.append(law_system)
                if category:
                    where_clauses.append("category = %s")
                    params.append(category)
                where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
                cur.execute(
                    f"SELECT id, institution, law_name, subject, publish_date, law_system FROM comp_fsc_directives "
                    f"{where_sql} ORDER BY publish_date DESC LIMIT %s OFFSET %s",
                    params + [PAGE_SIZE, offset],
                )
                rows = [{"id": r["id"], "col1": r.get("institution",""), "col2": r.get("law_system",""), "col3": (r.get("law_name") or "")[:40], "col4": (r.get("subject") or "")[:60], "col5": r.get("publish_date","")} for r in cur.fetchall()]
                headers = ["機構", "法規體系", "法規名稱", "主旨", "發布日"]
                cur.execute(
                    f"SELECT COUNT(*) as cnt FROM comp_fsc_directives {where_sql}",
                    params,
                )
                total = cur.fetchone()["cnt"]

            else:
                rows, headers, total = [], [], 0

        return {"rows": rows, "headers": headers, "page": page, "page_size": PAGE_SIZE, "total": total}
    except Exception as e:
        return {"rows": [], "headers": [], "total": 0, "error": str(e)}
    finally:
        conn.close()


@router.get("/compliance/detail")
def get_compliance_detail(
    type: str = Query("penalties"),
    id: int = Query(...),
    user=Depends(get_current_user),
):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if type == "penalties":
                cur.execute("SELECT * FROM comp_penalties WHERE id=%s", (id,))
                row = cur.fetchone()
                if not row: return {"error": "not found"}
                return {"type": type, "id": id, "fields": [
                    {"label": "裁罰類別", "value": row.get("category","")},
                    {"label": "機構", "value": row.get("institution","")},
                    {"label": "日期", "value": row.get("date","")},
                    {"label": "標題", "value": row.get("title","")},
                    {"label": "內文", "value": row.get("content",""), "long": True},
                ]}
            elif type == "regulations":
                cur.execute("SELECT * FROM comp_regulations WHERE id=%s", (id,))
                row = cur.fetchone()
                if not row: return {"error": "not found"}
                return {"type": type, "id": id, "fields": [
                    {"label": "類別", "value": row.get("category","")},
                    {"label": "日期", "value": row.get("date","")},
                    {"label": "標題", "value": row.get("title","")},
                    {"label": "內文", "value": row.get("content",""), "long": True},
                ]}
            elif type == "national":
                cur.execute("SELECT * FROM comp_national_laws WHERE id=%s", (id,))
                row = cur.fetchone()
                if not row: return {"error": "not found"}
                return {"type": type, "id": id, "fields": [
                    {"label": "法規名稱", "value": row.get("law_name","")},
                    {"label": "層級", "value": row.get("law_level","")},
                    {"label": "條文號", "value": row.get("article_no","")},
                    {"label": "條文類型", "value": row.get("article_type","")},
                    {"label": "條文內容", "value": row.get("article_content",""), "long": True},
                ]}
            elif type == "fsc":
                cur.execute("SELECT * FROM comp_fsc_directives WHERE id=%s", (id,))
                row = cur.fetchone()
                if not row: return {"error": "not found"}
                return {"type": type, "id": id, "fields": [
                    {"label": "機構", "value": row.get("institution","")},
                    {"label": "法規體系", "value": row.get("law_system","")},
                    {"label": "法規類別", "value": row.get("category","")},
                    {"label": "法規名稱", "value": row.get("law_name","")},
                    {"label": "發文字號", "value": row.get("document_no","")},
                    {"label": "公發布日", "value": row.get("publish_date","")},
                    {"label": "生效日期", "value": row.get("effective_date","")},
                    {"label": "異動性質", "value": row.get("change_type","")},
                    {"label": "生效狀態", "value": row.get("law_status","")},
                    {"label": "主旨", "value": row.get("subject","")},
                    {"label": "法規內容", "value": row.get("content",""), "long": True},
                ]}
            return {"error": "unknown type"}
    finally:
        conn.close()


@router.get("/compliance/filters")
def get_compliance_filters(user=Depends(get_current_user)):
    """Return distinct filter values for each compliance type."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT category FROM comp_penalties WHERE category IS NOT NULL ORDER BY category")
            penalty_categories = [r["category"] for r in cur.fetchall()]
            cur.execute("SELECT DISTINCT institution FROM comp_penalties WHERE institution IS NOT NULL ORDER BY institution")
            penalty_institutions = [r["institution"] for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT category FROM comp_regulations WHERE category IS NOT NULL ORDER BY category")
            reg_categories = [r["category"] for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT law_level FROM comp_national_laws WHERE law_level IS NOT NULL ORDER BY law_level")
            national_levels = [r["law_level"] for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT institution FROM comp_fsc_directives WHERE institution IS NOT NULL ORDER BY institution")
            fsc_institutions = [r["institution"] for r in cur.fetchall()]
            cur.execute("SELECT DISTINCT law_system FROM comp_fsc_directives WHERE law_system IS NOT NULL ORDER BY law_system")
            fsc_systems = [r["law_system"] for r in cur.fetchall()]

        return {
            "penalties": {"categories": penalty_categories, "institutions": penalty_institutions},
            "regulations": {"categories": reg_categories},
            "national": {"levels": national_levels},
            "fsc": {"institutions": fsc_institutions, "systems": fsc_systems},
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
