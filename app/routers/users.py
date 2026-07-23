from fastapi import Depends, APIRouter, Query
from app.models.schemas import UserUpdateRequest, UserPublic
from app.repositories.store import DataStore

from app.utils.response import success
from app.utils.time_utils import utc_now_iso
from app.utils.deps import AuthError, require_roles
from app.utils.pagination import paginate

USERS = DataStore().users.read()
router = APIRouter(prefix="/api/users", tags=["users"])


### Depends参数必须是函数，不能是协程（async 函数直接返回的是协程）
@router.get("")
async def get_user_list(
    _: dict = Depends(require_roles(["admin"])),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    users = DataStore().list_users()
    pub_users = [UserPublic(
        id = user["id"],
        username = user["username"],
        role = user["role"],
        is_active = user["is_active"],
        created_at = user["created_at"],
        updated_at = user["updated_at"]
    ).model_dump(mode="json") for user in users]
    return success(paginate(pub_users, page, page_size), message="get user list successfully", code=200)

@router.get("/{user_id}")
async def get_user(user_id: str, _: dict = Depends(require_roles(["admin"]))):
    user = DataStore().get_user_by_id(user_id)
    if user is None:
        raise AuthError("User not found", 404)
    pub_user = UserPublic(
        id = user["id"],
        username = user["username"],
        role = user["role"],
        is_active = user["is_active"],
        created_at = user["created_at"],
        updated_at = user["updated_at"]
    )
    return success(pub_user.model_dump(mode="json"), message="get user successfully", code=200)

@router.put("/{user_id}")
async def update_user(user_id: str, body: UserUpdateRequest, admin: dict = Depends(require_roles(["admin"]))):
    user = DataStore().get_user_by_id(user_id)
    if user is None:
        raise AuthError("User not found", 404)
    if admin["id"] == user_id and body.is_active == False:
        raise AuthError("Admin-user self cannot be deactivated", 403)
    user["role"] = body.role if body.role is not None else user["role"]
    user["is_active"] = body.is_active if body.is_active is not None else user["is_active"]
    user["updated_at"] = utc_now_iso() if body.is_active is not None or body.role is not None else user["updated_at"]
    DataStore().save_user(user)
    return success(message="update user successfully", code=200)