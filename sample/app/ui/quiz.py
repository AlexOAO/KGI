import gradio as gr
from app.models.quiz import get_questions
from app.services.quiz_service import grade_quiz


def build_quiz(state):
    with gr.Column(visible=False) as quiz_panel:
        gr.Markdown("## 模組測驗")
        quiz_md = gr.Markdown("載入測驗中...")
        answer_inputs = []
        for i in range(5):
            with gr.Row(visible=False) as row:
                q_label = gr.Markdown(f"Q{i+1}:")
                a_input = gr.Radio(choices=[], label="選擇答案", interactive=True)
                answer_inputs.append((row, q_label, a_input))
        submit_btn = gr.Button("提交答案", variant="primary")
        result_md = gr.Markdown("", visible=False)
        dashboard_btn = gr.Button("查看學習儀表板 →", visible=False)
    return quiz_panel, quiz_md, answer_inputs, submit_btn, result_md, dashboard_btn


def load_quiz(state):
    module_id = state.get("current_module_id")
    questions = get_questions(module_id, limit=5)
    state = {**state, "quiz_questions": questions, "current_question": 0, "quiz_answers": {}}
    return state, questions


def build_quiz_ui(questions):
    updates = []
    for i in range(5):
        if i < len(questions):
            q = questions[i]
            opts = q.get("options_json") or []
            updates.append((gr.update(visible=True), gr.update(value=f"**Q{i+1}:** {q['prompt']}"), gr.update(choices=opts, value=None)))
        else:
            updates.append((gr.update(visible=False), gr.update(), gr.update(choices=[], value=None)))
    return updates


def submit_quiz(state, *answers):
    questions = state.get("quiz_questions", [])
    answers_dict = {}
    for i, q in enumerate(questions):
        answers_dict[str(q["id"])] = answers[i] if i < len(answers) else ""

    module = state.get("current_module_id")
    sprint_id = state.get("sprint_id")
    user_id = state.get("user_id")

    from app.models.module import get_module
    m = get_module(module)
    topic_tag = m.get("topic_tag", "") if m else ""

    score, correct, total, _ = grade_quiz(user_id, sprint_id, module, questions, answers_dict, topic_tag)

    state = {**state, "view": "quiz_result"}
    result = f"""## 測驗結果
- **得分：** {score:.1f} 分
- **答對：** {correct} / {total} 題
- **評級：** {"優秀 🌟" if score >= 90 else "良好 👍" if score >= 75 else "及格 ✅" if score >= 60 else "需加強 📚"}

下次複習時間已排程（SM-2 間隔複習）。
"""
    return state, gr.update(value=result, visible=True), gr.update(visible=True)
