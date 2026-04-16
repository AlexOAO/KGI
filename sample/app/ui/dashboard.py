import gradio as gr
import pandas as pd
from app.services.dashboard_service import get_dashboard


def build_dashboard(state):
    with gr.Column(visible=False) as dashboard_panel:
        gr.Markdown("## 學習儀表板")
        stats_md = gr.Markdown("")
        mastery_plot = gr.BarPlot(
            x="topic",
            y="score",
            title="各主題掌握度",
            x_title="主題",
            y_title="平均得分",
            visible=False,
        )
        reviews_table = gr.Dataframe(
            headers=["主題標籤", "下次複習日", "間隔天數", "熟練度"],
            datatype=["str", "str", "number", "number"],
            label="複習排程",
        )
        back_btn = gr.Button("← 返回模組列表")
    return dashboard_panel, stats_md, mastery_plot, reviews_table, back_btn


def load_dashboard(state):
    import pandas as pd
    user_id = state.get("user_id")
    if not user_id:
        empty_df = pd.DataFrame({"topic": [], "score": []})
        return state, gr.update(value="請先登入"), gr.update(value=empty_df, visible=False), gr.update(value=[])
    data = get_dashboard(user_id)
    stats = f"""
**已完成模組：** {data['modules_completed']} 個
**連續學習天數：** {data['streak']} 天
"""
    mastery_rows = []
    for m in data.get("mastery", []):
        mastery_rows.append({
            "topic": m.get("topic_tag", "")[:20],
            "score": round(float(m.get("avg_score", 0)), 1),
        })

    reviews = []
    for r in data.get("reviews", []):
        reviews.append([
            r.get("concept_tag", ""),
            str(r.get("next_review_at", "")),
            r.get("interval_days", 0),
            round(float(r.get("ease_factor", 2.5)), 2),
        ])

    mastery_df = pd.DataFrame(mastery_rows) if mastery_rows else pd.DataFrame({"topic": [], "score": []})

    return (
        state,
        gr.update(value=stats),
        gr.update(value=mastery_df, visible=bool(mastery_rows)),
        gr.update(value=reviews),
    )
