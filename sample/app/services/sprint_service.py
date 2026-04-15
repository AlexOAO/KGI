from app.models.session import create_sprint_session, complete_sprint_session, create_learning_journey
from app.models.module import get_flashcards

def start_sprint(user_id: int, module_id: int) -> dict:
    """Start a sprint session, return session info."""
    session_id = create_sprint_session(user_id, module_id)
    cards = get_flashcards(module_id)
    return {"session_id": session_id, "flashcards": cards}

def end_sprint(session_id: int, tab_switch_count: int = 0,
               status: str = 'finished_early') -> None:
    """Mark sprint session as completed."""
    complete_sprint_session(session_id, tab_switch_count, status)

def link_quiz_to_sprint(sprint_session_id: int, attempt_id: int) -> int:
    """Create learning journey map entry."""
    return create_learning_journey(sprint_session_id, attempt_id)
