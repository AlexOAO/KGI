"""Search dispatcher + Markdown formatter for compliance knowledge base."""
from app.core.config import COMPLIANCE_PAGE_SIZE
from app.models.compliance import (
    search_penalties,
    search_regulations,
    search_national_laws,
    search_fsc_regs,
)


def _penalty_card(item: dict) -> str:
    content = (item.get("content") or "")[:200]
    return (
        f"---\n"
        f"**[{item['institution']}]** · {item['issued_date']} · {item['category']}\n\n"
        f"**{item['title'][:120]}**\n\n"
        f"{content}"
    )


def _regulation_card(item: dict) -> str:
    content = (item.get("content") or "")[:200]
    title = item.get("title", "")
    # Strip appended date suffix like "_2026-01-08"
    if "_20" in title:
        title = title[:title.rfind("_20")]
    return (
        f"---\n"
        f"**[{item['category']}]** · {item['issued_date']}\n\n"
        f"**{title[:120]}**\n\n"
        f"{content}"
    )


def _national_law_card(item: dict) -> str:
    content = (item.get("article_content") or "")[:200]
    return (
        f"---\n"
        f"**{item['law_name']}** · {item['law_level']} · {item['article_no']}\n\n"
        f"{content}"
    )


def _fsc_reg_card(item: dict) -> str:
    content = (item.get("content") or "")[:200]
    name = item.get("reg_name") or item.get("purpose") or ""
    return (
        f"---\n"
        f"**[{item['institution']}]** · {item['effective_date']} · {item['reg_category']}\n\n"
        f"**{name[:120]}**\n\n"
        f"{content}"
    )


_FORMATTERS = {
    "penalties":   (_penalty_card,    search_penalties),
    "regulations": (_regulation_card, search_regulations),
    "national":    (_national_law_card, search_national_laws),
    "fsc":         (_fsc_reg_card,    search_fsc_regs),
}

_EMPTY_MSG = {
    "penalties":   "請輸入 3 個以上字元進行裁罰案例搜尋。",
    "regulations": "請輸入 3 個以上字元進行監理函令搜尋。",
    "national":    "請輸入 3 個以上字元進行全國法規搜尋。",
    "fsc":         "請輸入 3 個以上字元進行主管法規搜尋。",
}


def search_compliance(query: str, collection: str, page: int = 1) -> dict:
    """Search one compliance collection and return formatted Markdown + page info.

    Returns:
        {
          "results_md": str,
          "page_info":  str,   # "第 1 / 5 頁（共 47 筆）"
          "has_prev":   bool,
          "has_next":   bool,
        }
    """
    fmt_fn, search_fn = _FORMATTERS[collection]

    if len(query) < 2:
        return {
            "results_md": _EMPTY_MSG[collection],
            "page_info": "",
            "has_prev": False,
            "has_next": False,
        }

    try:
        items, total = search_fn(query, page)
    except Exception as e:
        return {
            "results_md": f"搜尋發生錯誤：{e}",
            "page_info": "",
            "has_prev": False,
            "has_next": False,
        }

    if not items:
        return {
            "results_md": f"查無「{query}」相關結果。",
            "page_info": "",
            "has_prev": False,
            "has_next": False,
        }

    total_pages = max(1, (total + COMPLIANCE_PAGE_SIZE - 1) // COMPLIANCE_PAGE_SIZE)
    cards = "\n\n".join(fmt_fn(it) for it in items)

    return {
        "results_md": cards,
        "page_info": f"第 {page} / {total_pages} 頁（共 {total} 筆）",
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }
