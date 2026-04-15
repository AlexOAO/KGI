import gradio as gr

def create_dashboard_ui(app_state, handle_logout_fn, handle_restart_fn):
    with gr.Column(visible=False) as dashboard_col:
        gr.Markdown("## 學習儀表板")
        dash_welcome = gr.Markdown("")
        dash_stats = gr.Markdown("")
        dash_schedule = gr.Markdown("")
        dash_recent = gr.Markdown("")

        with gr.Row():
            restart_btn = gr.Button("繼續學習", variant="primary")
            logout_btn = gr.Button("登出")

        restart_btn.click(
            fn=handle_restart_fn,
            inputs=[app_state],
            outputs=[app_state, dashboard_col],
        )
        logout_btn.click(
            fn=handle_logout_fn,
            inputs=[app_state],
            outputs=[app_state, dashboard_col],
        )

    return dashboard_col, dash_welcome, dash_stats, dash_schedule, dash_recent
