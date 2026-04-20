from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.auth import get_current_user
from app.services.reward_service import (
    claim_level_reward, get_wallet, get_transaction_history,
)
from app.services.exchange_service import (
    convert_hours_to_points, convert_points_to_hours,
    redeem_catalog_item, get_catalog,
)
from app.core.database import get_conn

router = APIRouter(tags=["rewards"])


# ── Wallet & History ────────────────────────────────────────────

@router.get("/rewards/wallet")
def api_get_wallet(user=Depends(get_current_user)):
    return get_wallet(user["user_id"])


@router.get("/rewards/history")
def api_get_history(user=Depends(get_current_user)):
    return get_transaction_history(user["user_id"])


# ── Level-up Reward ─────────────────────────────────────────────

class ClaimLevelRewardRequest(BaseModel):
    level_reached: int
    reward_type: str   # 'kgi_points' | 'learning_hours'


@router.post("/rewards/claim-level")
def api_claim_level_reward(req: ClaimLevelRewardRequest, user=Depends(get_current_user)):
    return claim_level_reward(user["user_id"], req.level_reached, req.reward_type)


# ── Exchange ────────────────────────────────────────────────────

class ConvertRequest(BaseModel):
    direction: str   # 'hours_to_points' | 'points_to_hours'
    amount: float


@router.post("/rewards/convert")
def api_convert(req: ConvertRequest, user=Depends(get_current_user)):
    if req.direction == "hours_to_points":
        return convert_hours_to_points(user["user_id"], req.amount)
    elif req.direction == "points_to_hours":
        return convert_points_to_hours(user["user_id"], int(req.amount))
    else:
        raise HTTPException(status_code=400, detail="Invalid direction")


# ── Catalog & Redemption ────────────────────────────────────────

@router.get("/rewards/catalog")
def api_get_catalog(user=Depends(get_current_user)):
    return get_catalog(active_only=True)


class RedeemRequest(BaseModel):
    catalog_item_id: int


@router.post("/rewards/redeem")
def api_redeem(req: RedeemRequest, user=Depends(get_current_user)):
    return redeem_catalog_item(user["user_id"], req.catalog_item_id)


# ── Admin Endpoints ─────────────────────────────────────────────

def require_admin(user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


class CatalogItemRequest(BaseModel):
    name: str
    description: str = ""
    category: str = "gift"
    points_cost: int
    stock: int | None = None


@router.get("/admin/catalog")
def api_admin_catalog(user=Depends(require_admin)):
    return get_catalog(active_only=False)


@router.post("/admin/catalog")
def api_admin_create_item(req: CatalogItemRequest, user=Depends(require_admin)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO reward_catalog (name, description, category, points_cost, stock) "
                "VALUES (%s,%s,%s,%s,%s)",
                (req.name, req.description, req.category, req.points_cost, req.stock),
            )
            item_id = cur.lastrowid
        conn.commit()
        return {"ok": True, "id": item_id}
    finally:
        conn.close()


class UpdateCatalogRequest(BaseModel):
    name: str | None = None
    points_cost: int | None = None
    stock: int | None = None
    is_active: bool | None = None


@router.put("/admin/catalog/{item_id}")
def api_admin_update_item(item_id: int, req: UpdateCatalogRequest, user=Depends(require_admin)):
    fields, vals = [], []
    if req.name is not None:
        fields.append("name=%s"); vals.append(req.name)
    if req.points_cost is not None:
        fields.append("points_cost=%s"); vals.append(req.points_cost)
    if req.stock is not None:
        fields.append("stock=%s"); vals.append(req.stock)
    if req.is_active is not None:
        fields.append("is_active=%s"); vals.append(int(req.is_active))
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    vals.append(item_id)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE reward_catalog SET {', '.join(fields)} WHERE id=%s", vals)
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


class AdminGrantRequest(BaseModel):
    user_id: int
    kgi_points: int = 0
    learning_hours: float = 0.0
    note: str = ""


@router.post("/admin/grant")
def api_admin_grant(req: AdminGrantRequest, user=Depends(require_admin)):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if req.kgi_points:
                cur.execute(
                    "UPDATE users SET kgi_points = kgi_points + %s WHERE id=%s",
                    (req.kgi_points, req.user_id),
                )
                cur.execute(
                    "INSERT INTO reward_transactions (user_id, txn_type, points_delta, note) "
                    "VALUES (%s,'admin_grant_points',%s,%s)",
                    (req.user_id, req.kgi_points, req.note or "管理員補發點數"),
                )
            if req.learning_hours:
                cur.execute(
                    "UPDATE users SET learning_hours = learning_hours + %s WHERE id=%s",
                    (req.learning_hours, req.user_id),
                )
                cur.execute(
                    "INSERT INTO reward_transactions (user_id, txn_type, hours_delta, note) "
                    "VALUES (%s,'admin_grant_hours',%s,%s)",
                    (req.user_id, req.learning_hours, req.note or "管理員補發時數"),
                )
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()
