import gradio as gr
from app.core.database import get_conn


PAGE_SIZE = 10


def search_compliance(keyword: str, table: str, page: int = 1):
    if not keyword.strip():
        return [], 0
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            offset = (page - 1) * PAGE_SIZE
            if table == "penalties":
                cur.execute(
                    "SELECT id, institution, title, date FROM comp_penalties "
                    "WHERE MATCH(title, content) AGAINST(%s IN BOOLEAN MODE) LIMIT %s OFFSET %s",
                    (keyword, PAGE_SIZE, offset),
                )
                rows = [[r["id"], r.get("institution",""), r.get("title","")[:80], r.get("date","")] for r in cur.fetchall()]
                cur.execute("SELECT FOUND_ROWS() as cnt")
            elif table == "regulations":
                cur.execute(
                    "SELECT id, category, title, date FROM comp_regulations "
                    "WHERE MATCH(title, content) AGAINST(%s IN BOOLEAN MODE) LIMIT %s OFFSET %s",
                    (keyword, PAGE_SIZE, offset),
                )
                rows = [[r["id"], r.get("category",""), r.get("title","")[:80], r.get("date","")] for r in cur.fetchall()]
            elif table == "national":
                cur.execute(
                    "SELECT id, law_name, article_no, law_level FROM comp_national_laws "
                    "WHERE MATCH(law_name, article_content) AGAINST(%s IN BOOLEAN MODE) LIMIT %s OFFSET %s",
                    (keyword, PAGE_SIZE, offset),
                )
                rows = [[r["id"], r.get("law_name",""), r.get("article_no",""), r.get("law_level","")] for r in cur.fetchall()]
            elif table == "fsc":
                cur.execute(
                    "SELECT id, institution, law_name, subject, publish_date FROM comp_fsc_directives "
                    "WHERE MATCH(subject, content) AGAINST(%s IN BOOLEAN MODE) LIMIT %s OFFSET %s",
                    (keyword, PAGE_SIZE, offset),
                )
                rows = [[r["id"], r.get("institution",""), r.get("law_name","")[:40], r.get("subject","")[:60], r.get("publish_date","")] for r in cur.fetchall()]
            else:
                rows = []
        return rows
    except Exception as e:
        return [[str(e), "", "", ""]]
    finally:
        conn.close()


def build_compliance(state):
    with gr.Column(visible=False) as compliance_panel:
        gr.Markdown("## 法遵資料庫搜尋")
        with gr.Tabs():
            with gr.Tab("裁罰案例"):
                penalty_kw = gr.Textbox(label="關鍵字搜尋", placeholder="例：保險法")
                penalty_btn = gr.Button("搜尋")
                penalty_table = gr.Dataframe(
                    headers=["ID", "機構", "標題", "日期"],
                    datatype=["number", "str", "str", "str"],
                    label="裁罰結果",
                )
                penalty_btn.click(fn=lambda kw: search_compliance(kw, "penalties"), inputs=[penalty_kw], outputs=[penalty_table])

            with gr.Tab("函令法規"):
                reg_kw = gr.Textbox(label="關鍵字搜尋", placeholder="例：壽險")
                reg_btn = gr.Button("搜尋")
                reg_table = gr.Dataframe(
                    headers=["ID", "類別", "標題", "日期"],
                    datatype=["number", "str", "str", "str"],
                    label="函令結果",
                )
                reg_btn.click(fn=lambda kw: search_compliance(kw, "regulations"), inputs=[reg_kw], outputs=[reg_table])

            with gr.Tab("全國法規"):
                nat_kw = gr.Textbox(label="關鍵字搜尋", placeholder="例：保險法")
                nat_btn = gr.Button("搜尋")
                nat_table = gr.Dataframe(
                    headers=["ID", "法規名稱", "條文號", "法規層級"],
                    datatype=["number", "str", "str", "str"],
                    label="法規結果",
                )
                nat_btn.click(fn=lambda kw: search_compliance(kw, "national"), inputs=[nat_kw], outputs=[nat_table])

            with gr.Tab("主管法規"):
                fsc_kw = gr.Textbox(label="關鍵字搜尋", placeholder="例：洗錢防制")
                fsc_btn = gr.Button("搜尋")
                fsc_table = gr.Dataframe(
                    headers=["ID", "機構", "法規名稱", "主旨", "發布日"],
                    datatype=["number", "str", "str", "str", "str"],
                    label="主管法規結果",
                )
                fsc_btn.click(fn=lambda kw: search_compliance(kw, "fsc"), inputs=[fsc_kw], outputs=[fsc_table])

        back_btn = gr.Button("← 返回模組列表")
    return compliance_panel, back_btn
