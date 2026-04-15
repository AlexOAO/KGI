import gradio as gr

def create_quiz_ui(app_state, handle_submit_quiz_fn):
    with gr.Column(visible=False) as quiz_col:
        gr.Markdown("## 學習測驗")
        quiz_info = gr.Markdown("")

        # Dynamic question components (up to 5 questions)
        question_components = []
        for i in range(5):
            with gr.Group(visible=False) as qgroup:
                qlabel = gr.Markdown(f"問題 {i+1}")
                qradio = gr.Radio(choices=[], label="選擇答案", interactive=True)
            question_components.append((qgroup, qlabel, qradio))

        submit_btn = gr.Button("提交答案", variant="primary")
        quiz_result = gr.Markdown("")

        submit_btn.click(
            fn=handle_submit_quiz_fn,
            inputs=[app_state] + [qr for _, _, qr in question_components],
            outputs=[app_state, quiz_result, quiz_col] + [qg for qg, _, _ in question_components],
        )

    return quiz_col, quiz_info, question_components, quiz_result
