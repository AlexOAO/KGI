"""Test data models using in-memory SQLite."""
import pytest
import sqlite3
import os
import sys

# Ensure app uses in-memory DB for tests
os.environ["TEST_DB"] = ":memory:"

from app.core import database as db_module


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """Use a temporary database for each test."""
    test_db = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    db_module.init_db()
    yield
    if os.path.exists(test_db):
        os.remove(test_db)


def test_create_and_get_user():
    from app.models.user import create_user, get_user_by_username
    uid = create_user("testuser", "testpass", "learner")
    assert uid is not None
    user = get_user_by_username("testuser")
    assert user is not None
    assert user["username"] == "testuser"
    assert user["role"] == "learner"


def test_authenticate_valid():
    from app.models.user import create_user, authenticate
    create_user("authuser", "mypass", "learner")
    result = authenticate("authuser", "mypass")
    assert result is not None
    assert result["username"] == "authuser"
    assert result["token"] is not None


def test_authenticate_invalid():
    from app.models.user import create_user, authenticate
    create_user("authuser2", "mypass", "learner")
    result = authenticate("authuser2", "wrongpass")
    assert result is None


def test_create_and_get_module():
    from app.models.module import create_module, get_module_by_id, get_all_modules
    mid = create_module("Test Module", "test_tag", 300, "beginner")
    assert mid is not None
    module = get_module_by_id(mid)
    assert module["title"] == "Test Module"
    modules = get_all_modules()
    assert len(modules) >= 1


def test_create_flashcards():
    from app.models.module import create_module, create_flashcard, get_flashcards
    mid = create_module("Flash Module", "flash_tag")
    create_flashcard(mid, 1, "Card 1 content")
    create_flashcard(mid, 2, "Card 2 content")
    cards = get_flashcards(mid)
    assert len(cards) == 2
    assert cards[0]["text_content"] == "Card 1 content"


def test_create_question():
    from app.models.module import create_module
    from app.models.quiz import create_question, get_questions_by_module
    mid = create_module("Quiz Module", "quiz_tag")
    create_question(mid, "What is 2+2?", ["3", "4", "5"], "4")
    questions = get_questions_by_module(mid)
    assert len(questions) == 1
    assert questions[0]["question_text"] == "What is 2+2?"
    assert "4" in questions[0]["options"]
