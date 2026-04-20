from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.api.auth import get_current_user
from app.models.sprint import start_sprint, end_sprint, increment_tab_switch

router = APIRouter(tags=["sprint"])


class StartSprintRequest(BaseModel):
    module_id: int


class EndSprintRequest(BaseModel):
    sprint_id: int
    tab_switch_count: int = 0
    completion_status: str = "finished_early"


@router.post("/sprint/start")
def api_start_sprint(req: StartSprintRequest, user=Depends(get_current_user)):
    sprint_id = start_sprint(user["user_id"], req.module_id)
    return {"sprint_id": sprint_id}


@router.post("/sprint/end")
def api_end_sprint(req: EndSprintRequest, user=Depends(get_current_user)):
    end_sprint(req.sprint_id, req.tab_switch_count, req.completion_status)
    return {"ok": True}


class TabSwitchRequest(BaseModel):
    sprint_id: int


@router.post("/sprint/tab-switch")
def api_tab_switch(req: TabSwitchRequest, user=Depends(get_current_user)):
    increment_tab_switch(req.sprint_id)
    return {"ok": True}
