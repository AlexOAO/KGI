import gradio as gr

def create_reader_ui(app_state, handle_next_card_fn, handle_prev_card_fn, handle_timer_tick_fn, handle_finish_reading_fn, handle_tab_switch_fn, handle_tab_visible_fn):
    with gr.Column(visible=False) as reader_col:
        gr.Markdown("## 閱讀 Sprint")
        timer_display = gr.Textbox(
            label="剩餘時間",
            value="07:00",
            interactive=False,
            elem_id="timer-display"
        )
        card_counter = gr.Markdown("卡片 1 / 5")
        card_content = gr.Markdown("載入中...")

        with gr.Row():
            prev_btn = gr.Button("← 上一張", size="sm")
            next_btn = gr.Button("下一張 →", size="sm")

        finish_btn = gr.Button("完成閱讀 →", variant="primary")

        # Tab switch detection via JavaScript
        tab_switch_js = gr.HTML("""
<script>
(function() {
    function triggerHiddenButton(elemId) {
        var btn = document.getElementById(elemId);
        if (btn) { btn.click(); }
    }
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden') {
            triggerHiddenButton('tab-switch-trigger');
        } else {
            triggerHiddenButton('timer-resume-trigger');
        }
    });
})();
</script>
""")
        tab_switch_trigger = gr.Button(visible=False, elem_id="tab-switch-trigger")
        timer_resume_trigger = gr.Button(visible=False, elem_id="timer-resume-trigger")
        resume_toast = gr.Markdown(visible=False, value="歡迎回來。計時器已恢復。")

        timer = gr.Timer(value=1)

        timer.tick(
            fn=handle_timer_tick_fn,
            inputs=[app_state],
            outputs=[app_state, timer_display, reader_col],
        )
        prev_btn.click(
            fn=handle_prev_card_fn,
            inputs=[app_state],
            outputs=[app_state, card_content, card_counter],
        )
        next_btn.click(
            fn=handle_next_card_fn,
            inputs=[app_state],
            outputs=[app_state, card_content, card_counter],
        )
        finish_btn.click(
            fn=handle_finish_reading_fn,
            inputs=[app_state],
            outputs=[app_state, reader_col],
        )
        tab_switch_trigger.click(
            fn=handle_tab_switch_fn,
            inputs=[app_state],
            outputs=[app_state],
        )
        timer_resume_trigger.click(
            fn=handle_tab_visible_fn,
            inputs=[app_state],
            outputs=[app_state, resume_toast],
        )

    return reader_col, card_content, card_counter, timer_display, resume_toast
