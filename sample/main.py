import gradio as gr
from app.core.database import init_db, init_compliance_db
from app.core.config import TIMER_SECONDS, APP_HOST, APP_PORT
from app.data.seed import seed
from app.data.compliance_loader import load_all_compliance_data, generate_compliance_modules
from app.models.user import authenticate
from app.models.module import get_all_modules, get_module_by_id, get_flashcards
from app.models.quiz import get_questions_by_module
from app.services.sprint_service import start_sprint, end_sprint, link_quiz_to_sprint
from app.services.quiz_service import grade_quiz
from app.services.dashboard_service import get_dashboard_data
from app.services.compliance_service import search_compliance

DEFAULT_STATE = {
    "user_id": None,
    "username": None,
    "token": None,
    "current_module_id": None,
    "current_sprint_session_id": None,
    "current_card_index": 0,
    "timer_remaining": TIMER_SECONDS,
    "timer_paused": False,
    "tab_switch_count": 0,
    "quiz_questions": [],
    "quiz_answers": {},
    "flashcards": [],
    "sprint_active": False,
    "card_count": 0,
    "question_count": 0,
    "compliance_query": "",
    "compliance_pages": {"penalties": 1, "regulations": 1, "national": 1, "fsc": 1},
}

def format_timer(seconds: int) -> str:
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


def build_app_v2():
    """Build the complete Gradio app inline for proper event wiring."""
    with gr.Blocks(title="微學習平台", theme=gr.themes.Soft()) as demo:
        app_state = gr.State({**DEFAULT_STATE})

        # ── LOGIN ─────────────────────────────────────────────
        with gr.Column(visible=True) as login_col:
            gr.Markdown("# 微學習平台\n### 請登入以繼續")
            username_input = gr.Textbox(label="用戶名稱", placeholder="例如：learner1")
            password_input = gr.Textbox(label="密碼", type="password")
            login_btn = gr.Button("登入", variant="primary")
            login_msg = gr.Markdown("")

        # ── MODULE LIST ───────────────────────────────────────
        with gr.Column(visible=False) as module_col:
            gr.Markdown("## 選擇學習模組")
            module_radio = gr.Radio(choices=[], label="可用模組", interactive=True)
            with gr.Row():
                select_btn = gr.Button("開始學習", variant="primary")
                compliance_btn = gr.Button("合規查詢", variant="secondary")
            module_info = gr.Markdown("")

        # ── PRE-SPRINT ────────────────────────────────────────
        with gr.Column(visible=False) as pre_sprint_col:
            pre_title = gr.Markdown("## 準備開始 Sprint")
            pre_tag = gr.Markdown("")
            pre_warning = gr.Markdown("> 選擇模組後顯示詳細資訊")
            with gr.Row():
                back_btn = gr.Button("← 返回", size="sm")
                start_btn = gr.Button("開始 Sprint ▶", variant="primary", size="lg")

        # ── READER ────────────────────────────────────────────
        with gr.Column(visible=False) as reader_col:
            gr.Markdown("## 閱讀 Sprint")
            timer_display = gr.Textbox(label="剩餘時間", value="07:00", interactive=False)
            card_counter = gr.Markdown("卡片 1 / 5")
            card_content = gr.Markdown("載入中...")
            with gr.Row():
                prev_btn = gr.Button("← 上一張")
                next_btn = gr.Button("下一張 →")
            finish_btn = gr.Button("完成閱讀，進入測驗 →", variant="primary")
            tab_switch_js = gr.HTML("""
<script>
(function() {
    function triggerById(id) {
        var el = document.getElementById(id);
        if (el) { el.click(); }
    }
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden') {
            triggerById('tab-switch-trigger');
        } else {
            triggerById('timer-resume-trigger');
        }
    });
})();
</script>
""")
            tab_switch_trigger = gr.Button(visible=False, elem_id="tab-switch-trigger")
            timer_resume_trigger = gr.Button(visible=False, elem_id="timer-resume-trigger")
            resume_toast = gr.Markdown(visible=False, value="歡迎回來。計時器已恢復。")
            timer = gr.Timer(value=1)

        # ── QUIZ ──────────────────────────────────────────────
        with gr.Column(visible=False) as quiz_col:
            gr.Markdown("## 學習測驗")
            quiz_info = gr.Markdown("")
            q_groups = []
            q_labels = []
            q_radios = []
            for i in range(5):
                with gr.Group(visible=False) as qg:
                    ql = gr.Markdown(f"**問題 {i+1}**")
                    qr = gr.Radio(choices=[], label=f"問題 {i+1}", interactive=True)
                q_groups.append(qg)
                q_labels.append(ql)
                q_radios.append(qr)
            submit_btn = gr.Button("提交答案", variant="primary")
            quiz_result = gr.Markdown("")

        # ── DASHBOARD ─────────────────────────────────────────
        with gr.Column(visible=False) as dashboard_col:
            gr.Markdown("## 學習儀表板")
            dash_welcome = gr.Markdown("")
            dash_stats = gr.Markdown("")
            dash_schedule = gr.Markdown("")
            dash_recent = gr.Markdown("")
            with gr.Row():
                continue_btn = gr.Button("繼續學習", variant="primary")
                logout_btn = gr.Button("登出")

        # ── COMPLIANCE ────────────────────────────────────────
        with gr.Column(visible=False) as compliance_col:
            gr.Markdown("## 合規知識庫查詢")
            with gr.Row():
                search_input = gr.Textbox(
                    label="搜尋關鍵字",
                    placeholder="輸入 3 個以上字元，例如：保險法、裁罰...",
                    scale=4,
                )
                search_btn = gr.Button("搜尋", variant="primary", scale=1)
            with gr.Tabs():
                with gr.Tab("裁罰案例"):
                    penalties_results = gr.Markdown("輸入關鍵字後點擊搜尋")
                    penalties_page_info = gr.Markdown("")
                    with gr.Row():
                        pen_prev_btn = gr.Button("← 上頁", size="sm")
                        pen_next_btn = gr.Button("下頁 →", size="sm")
                with gr.Tab("監理函令"):
                    reg_results = gr.Markdown("輸入關鍵字後點擊搜尋")
                    reg_page_info = gr.Markdown("")
                    with gr.Row():
                        reg_prev_btn = gr.Button("← 上頁", size="sm")
                        reg_next_btn = gr.Button("下頁 →", size="sm")
                with gr.Tab("全國法規"):
                    nat_results = gr.Markdown("輸入關鍵字後點擊搜尋")
                    nat_page_info = gr.Markdown("")
                    with gr.Row():
                        nat_prev_btn = gr.Button("← 上頁", size="sm")
                        nat_next_btn = gr.Button("下頁 →", size="sm")
                with gr.Tab("主管法規"):
                    fsc_results = gr.Markdown("輸入關鍵字後點擊搜尋")
                    fsc_page_info = gr.Markdown("")
                    with gr.Row():
                        fsc_prev_btn = gr.Button("← 上頁", size="sm")
                        fsc_next_btn = gr.Button("下頁 →", size="sm")
            back_compliance_btn = gr.Button("← 返回模組")

        # ── EVENT HANDLERS ────────────────────────────────────

        def do_login(username, password, state):
            result = authenticate(username, password)
            if result:
                new_state = {**DEFAULT_STATE}
                new_state["user_id"] = result["user_id"]
                new_state["username"] = result["username"]
                new_state["token"] = result["token"]
                modules = get_all_modules()
                choices = [f"{m['id']}: {m['title']}" for m in modules]
                return (
                    new_state,
                    gr.update(value=f"歡迎，{result['username']}！"),
                    gr.update(visible=False),   # hide login
                    gr.update(visible=True),    # show modules
                    gr.update(choices=choices, value=None),
                )
            return (
                state,
                gr.update(value="用戶名或密碼錯誤"),
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(),
            )

        def do_select_module(module_choice, state):
            try:
                if not module_choice:
                    return state, gr.update(value="請先選擇一個模組"), \
                           gr.update(visible=True), gr.update(visible=False), \
                           gr.update(), gr.update(), gr.update()
                module_id = int(module_choice.split(":")[0].strip())
                cards = get_flashcards(module_id)
                questions = get_questions_by_module(module_id)
                card_count = len(cards)
                q_count = len(questions)
                state = {**state, "current_module_id": module_id,
                         "card_count": card_count, "question_count": q_count}
                module = get_module_by_id(module_id)
                title_md = f"## 準備開始 Sprint\n### {module['title']}"
                tag_md = f"**主題：** {module['topic_tag']} ｜ **難度：** {module['difficulty_level']} ｜ **時長：** {module['duration_seconds']//60} 分鐘"
                warning_md = (
                    f"> 您有 7 分鐘閱讀 **{card_count} 張卡片**。"
                    f"**{q_count} 題測驗**將在閱讀後立即開始。\n"
                    "> 切換標籤頁將被記錄。"
                )
                return (
                    state,
                    gr.update(value=""),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(value=title_md),
                    gr.update(value=tag_md),
                    gr.update(value=warning_md),
                )
            except Exception as e:
                return state, gr.update(value=f"⚠️ 錯誤：{e}"), \
                       gr.update(visible=True), gr.update(visible=False), \
                       gr.update(), gr.update(), gr.update()

        def do_back_to_modules(state):
            modules = get_all_modules()
            choices = [f"{m['id']}: {m['title']}" for m in modules]
            return (
                state,
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(choices=choices),
            )

        def do_start_sprint(state):
            user_id = state["user_id"]
            module_id = state["current_module_id"]
            sprint_info = start_sprint(user_id, module_id)
            new_state = {
                **state,
                "current_sprint_session_id": sprint_info["session_id"],
                "flashcards": sprint_info["flashcards"],
                "current_card_index": 0,
                "timer_remaining": TIMER_SECONDS,
                "timer_paused": False,
                "tab_switch_count": 0,
                "sprint_active": True,
            }
            cards = new_state["flashcards"]
            content = cards[0]["text_content"] if cards else "無卡片"
            counter = f"卡片 1 / {len(cards)}"
            return (
                new_state,
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(value=content),
                gr.update(value=counter),
                gr.update(value=format_timer(TIMER_SECONDS)),
            )

        def do_prev_card(state):
            idx = max(0, state.get("current_card_index", 0) - 1)
            cards = state.get("flashcards", [])
            new_state = {**state, "current_card_index": idx}
            content = cards[idx]["text_content"] if cards else "無卡片"
            counter = f"卡片 {idx + 1} / {len(cards)}"
            return new_state, gr.update(value=content), gr.update(value=counter)

        def do_next_card(state):
            cards = state.get("flashcards", [])
            idx = min(len(cards) - 1, state.get("current_card_index", 0) + 1)
            new_state = {**state, "current_card_index": idx}
            content = cards[idx]["text_content"] if cards else "無卡片"
            counter = f"卡片 {idx + 1} / {len(cards)}"
            return new_state, gr.update(value=content), gr.update(value=counter)

        def do_timer_tick(state):
            if not state.get("sprint_active", False) or state.get("timer_paused", False):
                return [gr.update()] * 5

            remaining = state.get("timer_remaining", TIMER_SECONDS)
            if remaining > 0:
                remaining -= 1
            new_state = {**state, "timer_remaining": remaining}
            timer_str = format_timer(remaining)

            if remaining <= 0:
                session_id = new_state.get("current_sprint_session_id")
                tab_switches = new_state.get("tab_switch_count", 0)
                if session_id:
                    end_sprint(session_id, tab_switches, 'timed_out')
                module_id = new_state.get("current_module_id")
                if module_id:
                    questions = get_questions_by_module(module_id)
                    new_state = {**new_state, "quiz_questions": questions,
                                 "sprint_active": False}
                return [new_state, gr.update(value="00:00"),
                        gr.update(visible=False), gr.update(visible=True), gr.update()]

            # Normal tick: only update timer text, do not change visibility
            return [new_state, gr.update(value=timer_str),
                    gr.update(), gr.update(), gr.update()]

        def do_finish_reading(state):
            session_id = state.get("current_sprint_session_id")
            tab_switches = state.get("tab_switch_count", 0)
            if session_id:
                end_sprint(session_id, tab_switches, 'finished_early')
            module_id = state["current_module_id"]
            questions = get_questions_by_module(module_id)
            new_state = {**state, "quiz_questions": questions, "quiz_answers": {},
                         "sprint_active": False}

            updates = [new_state, gr.update(visible=False), gr.update(visible=True)]
            for i in range(5):
                if i < len(questions):
                    q = questions[i]
                    updates += [
                        gr.update(visible=True),
                        gr.update(value=f"**問題 {i+1}：** {q['question_text']}"),
                        gr.update(choices=q["options"], value=None),
                    ]
                else:
                    updates += [gr.update(visible=False), gr.update(), gr.update(choices=[], value=None)]

            return updates

        def do_tab_switch(state):
            new_state = {
                **state,
                "tab_switch_count": state.get("tab_switch_count", 0) + 1,
                "timer_paused": True,
            }
            return new_state

        def do_tab_visible(state):
            new_state = {**state, "timer_paused": False}
            return new_state, gr.update(visible=True, value="歡迎回來。計時器已恢復。")

        def do_submit_quiz(state, *answers):
            user_id = state["user_id"]
            module_id = state["current_module_id"]
            sprint_session_id = state.get("current_sprint_session_id")
            questions = state.get("quiz_questions", [])

            answer_map = {}
            for i, q in enumerate(questions):
                if i < len(answers) and answers[i] is not None:
                    answer_map[q["id"]] = answers[i]

            result = grade_quiz(user_id, module_id, sprint_session_id, answer_map)
            if sprint_session_id and result["attempt_id"]:
                link_quiz_to_sprint(sprint_session_id, result["attempt_id"])

            correct = result["score"]
            total = result["total"]
            accuracy = result["accuracy"]
            msg_lines = [f"## 測驗結果\n**得分：{correct}/{total}（{accuracy:.1f}%）**\n"]
            for r in result["results"]:
                icon = "正確" if r["is_correct"] else "錯誤"
                msg_lines.append(f"[{icon}] {r['question_text']}")
                if not r["is_correct"]:
                    msg_lines.append(f"  - 您的答案：{r['user_answer'] or '未作答'}")
                    msg_lines.append(f"  - 正確答案：{r['correct_answer']}")

            dash_data = get_dashboard_data(user_id)
            username = state.get("username", "學習者")
            dash_welcome_val = f"### 歡迎回來，{username}！"
            streak = dash_data["streak"]
            avg_acc = dash_data["avg_accuracy"]
            total_att = dash_data["total_attempts"]
            stats_md = (
                f"**連續學習天數：** {streak} 天\n\n"
                f"**總測驗次數：** {total_att}\n\n"
                f"**平均正確率：** {avg_acc:.1f}%\n\n"
                "**各模組掌握度：**\n"
            )
            for mid, acc in dash_data["mastery_by_module"].items():
                mod = get_module_by_id(mid)
                if mod:
                    bar = "█" * int(acc / 10) + "░" * (10 - int(acc / 10))
                    stats_md += f"- {mod['title']}: {bar} {acc:.0f}%\n"

            schedules = dash_data["review_schedule"]
            sched_md = "**複習排程：**\n" if schedules else "目前沒有複習排程。"
            for s in schedules[:5]:
                sched_md += f"- {s['module_title']}：{s['next_review_at'][:10]}（間隔 {s['interval_days']:.0f} 天）\n"

            recent = dash_data["recent_attempts"]
            recent_md = "**近期測驗：**\n" if recent else "尚無測驗記錄。"
            for a in recent:
                recent_md += f"- {a['module_title']}：{a['accuracy']:.0f}%（{a['completed_at'][:10]}）\n"

            hidden_groups = [gr.update(visible=False)] * 5

            return (
                state,
                gr.update(value="\n".join(msg_lines)),
                gr.update(visible=False),   # hide quiz
                *hidden_groups,
                gr.update(visible=True),    # show dashboard
                gr.update(value=dash_welcome_val),
                gr.update(value=stats_md),
                gr.update(value=sched_md),
                gr.update(value=recent_md),
            )

        def do_logout(state):
            from app.core.auth import destroy_session
            token = state.get("token")
            if token:
                destroy_session(token)
            return (
                {**DEFAULT_STATE},
                gr.update(visible=False),   # hide dashboard
                gr.update(visible=False),   # hide compliance
                gr.update(visible=True),    # show login
                gr.update(value=""),
                gr.update(value=""),
            )

        # ── COMPLIANCE HANDLERS ───────────────────────────────

        def do_show_compliance(state):
            return gr.update(visible=False), gr.update(visible=True)

        def do_back_compliance(state):
            modules = get_all_modules()
            choices = [f"{m['id']}: {m['title']}" for m in modules]
            return (
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(choices=choices),
            )

        def do_search_compliance(query, state):
            new_state = {
                **state,
                "compliance_query": query,
                "compliance_pages": {"penalties": 1, "regulations": 1, "national": 1, "fsc": 1},
            }
            pen = search_compliance(query, "penalties", 1)
            reg = search_compliance(query, "regulations", 1)
            nat = search_compliance(query, "national", 1)
            fsc = search_compliance(query, "fsc", 1)
            return (
                new_state,
                gr.update(value=pen["results_md"]),
                gr.update(value=pen["page_info"]),
                gr.update(value=reg["results_md"]),
                gr.update(value=reg["page_info"]),
                gr.update(value=nat["results_md"]),
                gr.update(value=nat["page_info"]),
                gr.update(value=fsc["results_md"]),
                gr.update(value=fsc["page_info"]),
            )

        def _paginate(state, collection, delta):
            query = state.get("compliance_query", "")
            pages = dict(state.get("compliance_pages", {"penalties": 1, "regulations": 1, "national": 1, "fsc": 1}))
            new_page = max(1, pages[collection] + delta)
            pages[collection] = new_page
            new_state = {**state, "compliance_pages": pages}
            res = search_compliance(query, collection, new_page)
            return new_state, gr.update(value=res["results_md"]), gr.update(value=res["page_info"])

        def do_pen_prev(state):   return _paginate(state, "penalties", -1)
        def do_pen_next(state):   return _paginate(state, "penalties", +1)
        def do_reg_prev(state):   return _paginate(state, "regulations", -1)
        def do_reg_next(state):   return _paginate(state, "regulations", +1)
        def do_nat_prev(state):   return _paginate(state, "national", -1)
        def do_nat_next(state):   return _paginate(state, "national", +1)
        def do_fsc_prev(state):   return _paginate(state, "fsc", -1)
        def do_fsc_next(state):   return _paginate(state, "fsc", +1)

        def do_continue_learning(state):
            modules = get_all_modules()
            choices = [f"{m['id']}: {m['title']}" for m in modules]
            return (
                state,
                gr.update(visible=False),   # hide dashboard
                gr.update(visible=True),    # show modules
                gr.update(choices=choices, value=None),
            )

        # ── WIRE EVENTS ───────────────────────────────────────

        login_btn.click(
            fn=do_login,
            inputs=[username_input, password_input, app_state],
            outputs=[app_state, login_msg, login_col, module_col, module_radio],
        )
        password_input.submit(
            fn=do_login,
            inputs=[username_input, password_input, app_state],
            outputs=[app_state, login_msg, login_col, module_col, module_radio],
        )

        select_btn.click(
            fn=do_select_module,
            inputs=[module_radio, app_state],
            outputs=[app_state, module_info, module_col, pre_sprint_col, pre_title, pre_tag, pre_warning],
        )

        back_btn.click(
            fn=do_back_to_modules,
            inputs=[app_state],
            outputs=[app_state, pre_sprint_col, module_col, module_radio],
        )

        start_btn.click(
            fn=do_start_sprint,
            inputs=[app_state],
            outputs=[app_state, pre_sprint_col, reader_col, card_content, card_counter, timer_display],
        )

        prev_btn.click(
            fn=do_prev_card,
            inputs=[app_state],
            outputs=[app_state, card_content, card_counter],
        )

        next_btn.click(
            fn=do_next_card,
            inputs=[app_state],
            outputs=[app_state, card_content, card_counter],
        )

        timer.tick(
            fn=do_timer_tick,
            inputs=[app_state],
            outputs=[app_state, timer_display, reader_col, quiz_col, quiz_info],
            concurrency_limit=1,
        )

        finish_btn.click(
            fn=do_finish_reading,
            inputs=[app_state],
            outputs=[app_state, reader_col, quiz_col]
            + [item for triple in zip(q_groups, q_labels, q_radios) for item in triple],
        )

        tab_switch_trigger.click(
            fn=do_tab_switch,
            inputs=[app_state],
            outputs=[app_state],
        )

        timer_resume_trigger.click(
            fn=do_tab_visible,
            inputs=[app_state],
            outputs=[app_state, resume_toast],
        )

        submit_btn.click(
            fn=do_submit_quiz,
            inputs=[app_state] + q_radios,
            outputs=[app_state, quiz_result, quiz_col]
            + q_groups
            + [dashboard_col, dash_welcome, dash_stats, dash_schedule, dash_recent],
        )

        logout_btn.click(
            fn=do_logout,
            inputs=[app_state],
            outputs=[app_state, dashboard_col, compliance_col, login_col, username_input, password_input],
        )

        continue_btn.click(
            fn=do_continue_learning,
            inputs=[app_state],
            outputs=[app_state, dashboard_col, module_col, module_radio],
        )

        # ── COMPLIANCE EVENTS ─────────────────────────────────

        compliance_btn.click(
            fn=do_show_compliance,
            inputs=[app_state],
            outputs=[module_col, compliance_col],
        )

        back_compliance_btn.click(
            fn=do_back_compliance,
            inputs=[app_state],
            outputs=[compliance_col, module_col, module_radio],
        )

        _search_outputs = [
            app_state,
            penalties_results, penalties_page_info,
            reg_results, reg_page_info,
            nat_results, nat_page_info,
            fsc_results, fsc_page_info,
        ]
        search_btn.click(
            fn=do_search_compliance,
            inputs=[search_input, app_state],
            outputs=_search_outputs,
        )
        search_input.submit(
            fn=do_search_compliance,
            inputs=[search_input, app_state],
            outputs=_search_outputs,
        )

        pen_prev_btn.click(fn=do_pen_prev, inputs=[app_state],
                           outputs=[app_state, penalties_results, penalties_page_info])
        pen_next_btn.click(fn=do_pen_next, inputs=[app_state],
                           outputs=[app_state, penalties_results, penalties_page_info])
        reg_prev_btn.click(fn=do_reg_prev, inputs=[app_state],
                           outputs=[app_state, reg_results, reg_page_info])
        reg_next_btn.click(fn=do_reg_next, inputs=[app_state],
                           outputs=[app_state, reg_results, reg_page_info])
        nat_prev_btn.click(fn=do_nat_prev, inputs=[app_state],
                           outputs=[app_state, nat_results, nat_page_info])
        nat_next_btn.click(fn=do_nat_next, inputs=[app_state],
                           outputs=[app_state, nat_results, nat_page_info])
        fsc_prev_btn.click(fn=do_fsc_prev, inputs=[app_state],
                           outputs=[app_state, fsc_results, fsc_page_info])
        fsc_next_btn.click(fn=do_fsc_next, inputs=[app_state],
                           outputs=[app_state, fsc_results, fsc_page_info])

    return demo


if __name__ == "__main__":
    print("初始化資料庫...")
    init_db()
    print("載入種子資料...")
    seed()
    print("初始化合規資料庫 schema...")
    init_compliance_db()
    print("載入合規資料（首次約 15–30 秒）...")
    load_all_compliance_data()
    print("生成合規學習模組...")
    generate_compliance_modules()
    print("啟動應用程式...")
    app = build_app_v2()
    app.launch(server_name=APP_HOST, server_port=APP_PORT)
