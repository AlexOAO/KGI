import gradio as gr
from app.models.user import authenticate


def login_fn(username, password, state):
    user = authenticate(username, password)
    if not user:
        return state, gr.update(value="帳號或密碼錯誤"), gr.update(visible=True), gr.update(visible=False)
    state = {**state, "user_id": user["id"], "username": user["username"], "view": "modules"}
    return state, gr.update(value=""), gr.update(visible=False), gr.update(visible=True)


def build_login(state):
    with gr.Column(visible=True) as login_panel:
        gr.Markdown("## KGI 法遵合規微學習平台\n### 登入")
        username_input = gr.Textbox(label="帳號", placeholder="learner1")
        password_input = gr.Textbox(label="密碼", type="password", placeholder="pass123")
        login_btn = gr.Button("登入", variant="primary")
        error_msg = gr.Textbox(label="", visible=True, interactive=False, value="")
    return login_panel, username_input, password_input, login_btn, error_msg
