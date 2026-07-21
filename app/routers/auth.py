from fastapi import Depends, Request, APIRouter
from app.models.schemas import RegisterRequest, LoginRequest, UserPublic
from app.repositories.store import DataStore

from app.utils.response import success, error
from app.utils.ids import new_uuid
from app.utils.security import hash_password, verify_password
from app.utils.time_utils import utc_now_iso
from app.utils.deps import get_current_user

USERS = DataStore().users.read()
router = APIRouter(prefix="/api/auth", tags=["auth"])


# # /api/auth/*

@router.post("/register")
async def register(body: RegisterRequest):
    # 用户已存在
    if DataStore().get_user_by_username(body.username) is not None:
        return error("username already exists", code = 409, data = None)
    now = utc_now_iso()
    user = {
        "id": new_uuid(),
        "username": body.username,
        "password_hash": hash_password(body.password),
        "role": "student",  # 注册默认学生
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    DataStore().save_user(user)
    pub_user = UserPublic(
        id = user["id"],
        username = user["username"],
        role = user["role"],
        is_active = user["is_active"],
        created_at = user["created_at"],
        updated_at = user["updated_at"]
    )
    return success(pub_user.model_dump(mode="json"), message="registered", code=201)


@router.post("/login")
async def login(request: Request, body: LoginRequest):
    user = DataStore().get_user_by_username(body.username)
    # 用户不存在
    if user is None:
        return error("authentication failed", code = 401, data = None)
    # 密码错误
    if not verify_password(body.password, user["password_hash"]):
        return error("authentication failed", code = 401, data = None)
    if user["is_active"] is False:
        return error("authentication failed", code = 403, data = None)
    pub_user = UserPublic(
        id = user["id"],
        username = user["username"],
        role = user["role"],
        is_active = user["is_active"],
        created_at = user["created_at"],
        updated_at = user["updated_at"]
    )
    request.session["user_id"] = user["id"]
    return success(pub_user.model_dump(mode="json"), message="logged in", code=200)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return success(message="logged out", code=200)


# # /api/users/*

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    me = UserPublic(
        id = user["id"],
        username = user["username"],
        role = user["role"],
        is_active = user["is_active"],
        created_at = user["created_at"],
        updated_at = user["updated_at"]
    )
    return success(me.model_dump(mode="json"), message="get me successfully", code=200)
### Depends参数必须是函数，不能是协程（async 函数直接返回的是协程）