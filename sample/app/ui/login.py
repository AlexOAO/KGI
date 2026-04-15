import gradio as gr

def create_login_ui(app_state, handle_login_fn):
    with gr.Column(visible=True) as login_col:
        gr.Markdown("# 微學習平台\n### 請登入以繼續")
        username_input = gr.Textbox(label="用戶名稱", placeholder="例如：learner1")
        password_input = gr.Textbox(label="密碼", type="password", placeholder="輸入密碼")
        login_btn = gr.Button("登入", variant="primary")
        login_msg = gr.Markdown("")

        login_btn.click(
            fn=handle_login_fn,
            inputs=[username_input, password_input, app_state],
            outputs=[app_state, login_msg, login_col],
        )
        password_input.submit(
            fn=handle_login_fn,
            inputs=[username_input, password_input, app_state],
            outputs=[app_state, login_msg, login_col],
        )

    return login_col, login_msg
