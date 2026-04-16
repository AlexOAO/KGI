import gradio as gr
from app.models.sprint import start_sprint, end_sprint
from app.core.config import TIMER_SECONDS


TAB_SWITCH_JS = """
<script>
(function() {
    if (window._kgiVisInit) return;
    window._kgiVisInit = true;
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden') {
            var el = document.getElementById('tab-switch-hidden');
            if (el) {
                var v = parseInt(el.value || '0') + 1;
                el.value = v;
                el.dispatchEvent(new Event('input', {bubbles: true}));
            }
        }
    });
})();
</script>
"""


def build_reader(state):
    with gr.Column(visible=False) as reader_panel:
        gr.HTML(TAB_SWITCH_JS)
        progress_md = gr.Markdown("Card 1 of 5")
        timer_display = gr.Markdown("⏱ 07:00")
        resume_notice = gr.Markdown("", visible=False)
        card_html = gr.HTML("<div style='padding:20px;font-size:1.1em;'>Loading...</div>")
        next_btn = gr.Button("下一張 →", variant="primary")
        finish_btn = gr.Button("完成閱讀 ✓", variant="secondary", visible=False)
        timer_component = gr.Timer(value=1, active=False)
        tab_switch_counter = gr.Number(value=0, visible=False, elem_id="tab-switch-hidden")
    return reader_panel, progress_md, timer_display, resume_notice, card_html, next_btn, finish_btn, timer_component, tab_switch_counter


def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"⏱ {m:02d}:{s:02d}"


def render_card(flashcards, index):
    if not flashcards or index >= len(flashcards):
        return "<div style='padding:20px;'>閱讀完畢</div>"
    card = flashcards[index]
    text = card.get("page_text") or ""
    return f"""<div style='background:#f8f9fa;border-radius:12px;padding:24px;font-size:1.1em;line-height:1.8;min-height:200px;'>
<p>{text}</p>
</div>"""


def start_sprint_fn(state):
    user_id = state.get("user_id")
    module_id = state.get("current_module_id")
    flashcards = state.get("flashcards", [])
    sprint_id = start_sprint(user_id, module_id)
    state = {
        **state,
        "sprint_id": sprint_id,
        "card_index": 0,
        "timer_remaining": TIMER_SECONDS,
        "timer_paused": False,
        "tab_switch_count": 0,
        "view": "reading",
    }
    total = len(flashcards)
    progress = f"Card 1 of {total}"
    timer_txt = format_time(TIMER_SECONDS)
    card = render_card(flashcards, 0)
    show_finish = total <= 1
    return (
        state,
        gr.update(value=progress),
        gr.update(value=timer_txt),
        gr.update(value=card),
        gr.update(active=True),
        gr.update(visible=not show_finish),
        gr.update(visible=show_finish),
    )


def tick_timer(state):
    if state.get("view") != "reading":
        return state, gr.update(), gr.update(), gr.update(active=False)
    remaining = state.get("timer_remaining", 0)
    if remaining <= 0:
        end_sprint(state["sprint_id"], state.get("tab_switch_count", 0), "timed_out")
        state = {**state, "view": "quiz", "timer_remaining": 0}
        return state, gr.update(value="⏱ 00:00"), gr.update(), gr.update(active=False)
    remaining -= 1
    state = {**state, "timer_remaining": remaining}
    timer_txt = format_time(remaining)
    if remaining == 0:
        end_sprint(state["sprint_id"], state.get("tab_switch_count", 0), "timed_out")
        state = {**state, "view": "quiz"}
        return state, gr.update(value="⏱ 00:00"), gr.update(), gr.update(active=False)
    return state, gr.update(value=timer_txt), gr.update(), gr.update(active=True)


def next_card_fn(state):
    flashcards = state.get("flashcards", [])
    idx = state.get("card_index", 0) + 1
    total = len(flashcards)
    state = {**state, "card_index": idx}
    if idx >= total:
        end_sprint(state["sprint_id"], state.get("tab_switch_count", 0), "finished_early")
        state = {**state, "view": "quiz"}
        return state, gr.update(), gr.update(), gr.update(), gr.update(active=False), gr.update(visible=True), gr.update(visible=False)
    progress = f"Card {idx+1} of {total}"
    card = render_card(flashcards, idx)
    show_finish = idx >= total - 1
    return (
        state,
        gr.update(value=progress),
        gr.update(value=card),
        gr.update(),
        gr.update(active=True),
        gr.update(visible=not show_finish),
        gr.update(visible=show_finish),
    )


def update_tab_switch(tab_count, state):
    state = {**state, "tab_switch_count": int(tab_count)}
    return state
