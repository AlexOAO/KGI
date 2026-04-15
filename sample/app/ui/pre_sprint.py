import gradio as gr

def create_pre_sprint_ui(app_state, handle_start_sprint_fn, handle_back_fn):
    with gr.Column(visible=False) as pre_sprint_col:
        pre_title = gr.Markdown("## 準備開始 Sprint")
        pre_tag = gr.Markdown("")
        pre_warning = gr.Markdown(
            "> **注意：** 本次 Sprint 為 7 分鐘計時學習。\n"
            "> 請確保您已準備好，並在學習過程中保持專注。\n"
            "> 切換標籤頁將被記錄。"
        )
        start_btn = gr.Button("開始 Sprint", variant="primary", size="lg")
        back_btn = gr.Button("返回", size="sm")

        start_btn.click(
            fn=handle_start_sprint_fn,
            inputs=[app_state],
            outputs=[app_state, pre_sprint_col],
        )
        back_btn.click(
            fn=handle_back_fn,
            inputs=[app_state],
            outputs=[app_state, pre_sprint_col],
        )

    return pre_sprint_col, pre_title, pre_tag
