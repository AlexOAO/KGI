"""Test quiz service including SM-2 integration."""
import pytest
import os

from app.core import database as db_module


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "quiz_test.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    db_module.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture
def sample_data():
    from app.models.user import create_user
    from app.models.module import create_module, create_flashcard
    from app.models.quiz import create_question
    uid = create_user("quizuser", "pass123", "learner")
    mid = create_module("Quiz Test Module", "quiz_topic")
    create_flashcard(mid, 1, "Study card")
    q1 = create_question(mid, "Q1?", ["A", "B", "C"], "A")
    q2 = create_question(mid, "Q2?", ["X", "Y", "Z"], "X")
    return {"user_id": uid, "module_id": mid, "q1": q1, "q2": q2}


def test_grade_quiz_perfect_score(sample_data):
    from app.services.quiz_service import grade_quiz
    answers = {
        sample_data["q1"]: "A",
        sample_data["q2"]: "X",
    }
    result = grade_quiz(sample_data["user_id"], sample_data["module_id"], None, answers)
    assert result["score"] == 2
    assert result["accuracy"] == 100.0
    assert result["total"] == 2


def test_grade_quiz_zero_score(sample_data):
    from app.services.quiz_service import grade_quiz
    answers = {
        sample_data["q1"]: "B",
        sample_data["q2"]: "Y",
    }
    result = grade_quiz(sample_data["user_id"], sample_data["module_id"], None, answers)
    assert result["score"] == 0
    assert result["accuracy"] == 0.0


def test_grade_quiz_creates_review_schedule(sample_data):
    from app.services.quiz_service import grade_quiz
    from app.models.schedule import get_schedule
    answers = {sample_data["q1"]: "A", sample_data["q2"]: "X"}
    grade_quiz(sample_data["user_id"], sample_data["module_id"], None, answers)
    schedule = get_schedule(sample_data["user_id"], sample_data["module_id"])
    assert schedule is not None
    assert schedule["repetitions"] >= 0


def test_grade_quiz_updates_sm2_on_repeat(sample_data):
    from app.services.quiz_service import grade_quiz
    from app.models.schedule import get_schedule
    answers = {sample_data["q1"]: "A", sample_data["q2"]: "X"}
    grade_quiz(sample_data["user_id"], sample_data["module_id"], None, answers)
    s1 = get_schedule(sample_data["user_id"], sample_data["module_id"])
    grade_quiz(sample_data["user_id"], sample_data["module_id"], None, answers)
    s2 = get_schedule(sample_data["user_id"], sample_data["module_id"])
    assert s2["repetitions"] > s1["repetitions"]
