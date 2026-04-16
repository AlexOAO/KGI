import gradio as gr
from app.models.module import get_module, get_flashcards
from app.models.quiz import get_questions


def build_pre_sprint(state):
    with gr.Column(visible=False) as pre_sprint_panel:
        gr.Markdown("## 學習衝刺準備")
        module_title = gr.Markdown("### 模組標題")
        module_tags = gr.Markdown("")
        warning_banner = gr.Markdown(
            "> ⚠️ 您有 **7 分鐘** 閱讀本模組的閃卡。閱讀結束後將立即進行 **5 題** 測驗。"
        )
        card_count_info = gr.Markdown("")
        start_btn = gr.Button("▶ 開始衝刺", variant="primary")
        back_btn = gr.Button("← 返回模組列表")
    return pre_sprint_panel, module_title, module_tags, card_count_info, start_btn, back_btn


def load_pre_sprint(module_id, state):
    if not module_id:
        return state, "### 請選擇模組", "", ""
    module_id = int(module_id)
    module = get_module(module_id)
    if not module:
        return state, "### 模組不存在", "", ""
    flashcards = get_flashcards(module_id)
    state = {**state, "current_module_id": module_id, "flashcards": flashcards, "card_index": 0, "view": "pre_sprint"}
    title = f"### {module['title']}"
    tags = f"**標籤：** {module.get('topic_tag', '')}"
    info = f"📄 共 **{len(flashcards)}** 張閃卡 | ⏱ {module['duration_seconds']//60} 分鐘"
    return state, title, tags, info
