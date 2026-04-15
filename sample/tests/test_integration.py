"""End-to-end integration tests."""
import pytest
import os

from app.core import database as db_module


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "integration_test.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    db_module.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


def test_full_learning_flow():
    """Test complete flow: register -> sprint -> quiz -> dashboard."""
    from app.models.user import create_user, authenticate
    from app.models.module import create_module, create_flashcard
    from app.models.quiz import create_question
    from app.services.sprint_service import start_sprint, end_sprint, link_quiz_to_sprint
    from app.services.quiz_service import grade_quiz
    from app.services.dashboard_service import get_dashboard_data

    # 1. Create user
    uid = create_user("integuser", "testpass", "learner")
    auth_result = authenticate("integuser", "testpass")
    assert auth_result is not None

    # 2. Create module with content
    mid = create_module("Integration Module", "integration_tag")
    create_flashcard(mid, 1, "Flashcard content")
    q1 = create_question(mid, "What is integration?", ["testing", "building", "both", "neither"], "testing")

    # 3. Sprint
    sprint_info = start_sprint(uid, mid)
    session_id = sprint_info["session_id"]
    assert len(sprint_info["flashcards"]) == 1
    end_sprint(session_id, tab_switch_count=0)

    # 4. Quiz
    result = grade_quiz(uid, mid, session_id, {q1: "testing"})
    assert result["score"] == 1
    assert result["accuracy"] == 100.0
    link_quiz_to_sprint(session_id, result["attempt_id"])

    # 5. Dashboard
    dash = get_dashboard_data(uid)
    assert dash["total_attempts"] == 1
    assert dash["avg_accuracy"] == 100.0
    assert mid in dash["mastery_by_module"]


def test_seed_is_idempotent():
    """Seed should not create duplicate records."""
    from app.data.seed import seed
    seed()
    seed()  # Call twice
    from app.models.user import get_user_by_username
    user = get_user_by_username("learner1")
    assert user is not None
    from app.core.database import get_connection
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users WHERE username='learner1'").fetchone()[0]
    assert count == 1
