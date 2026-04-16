import gradio as gr
from app.models.module import get_modules
from app.services.dashboard_service import get_due_reviews


def get_module_table(user_id):
    modules = get_modules()
    if not modules:
        return [], []
    due = get_due_reviews(user_id) if user_id else []
    due_tags = {r["concept_tag"] for r in due}
    rows = []
    for m in modules:
        tag = m.get("topic_tag", "")
        badge = "🔔 複習到期" if any(t in tag for t in due_tags) else ""
        rows.append([m["id"], m["title"], tag, f"{m['duration_seconds']//60} 分鐘", badge])
    return rows, [m["id"] for m in modules]


def build_module_list(state):
    with gr.Column(visible=False) as modules_panel:
        gr.Markdown("## 學習模組列表")
        due_badge = gr.Markdown("")
        module_table = gr.Dataframe(
            headers=["ID", "模組名稱", "主題標籤", "時長", "狀態"],
            datatype=["number", "str", "str", "str", "str"],
            interactive=False,
            label="可用模組",
        )
        selected_module_id = gr.Number(label="選擇模組 ID", precision=0)
        select_btn = gr.Button("進入模組", variant="primary")
        logout_btn = gr.Button("登出")
    return modules_panel, module_table, selected_module_id, select_btn, logout_btn, due_badge
