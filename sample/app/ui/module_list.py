import gradio as gr

def create_module_list_ui(app_state, handle_select_module_fn):
    with gr.Column(visible=False) as module_col:
        gr.Markdown("## 學習模組")
        module_radio = gr.Radio(choices=[], label="選擇模組", interactive=True)
        refresh_btn = gr.Button("重新載入模組", size="sm")
        select_btn = gr.Button("開始學習", variant="primary")
        module_info = gr.Markdown("")

        select_btn.click(
            fn=handle_select_module_fn,
            inputs=[module_radio, app_state],
            outputs=[app_state, module_info, module_col],
        )

    return module_col, module_radio, refresh_btn, module_info
