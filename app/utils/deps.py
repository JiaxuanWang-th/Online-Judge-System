"""放置依赖函数"""

from fastapi import Depends, Request
from app.repositories.store import DataStore

from typing import Callable


class AuthError(Exception):
    def __init__(self, message: str, code: int):
        self.message = message
        self.code = code


# 返回完全版的user（包含password_hash）
async def get_current_user(request: Request) -> dict:
    user_id = request.session.get("user_id")
    if user_id is None:
        raise AuthError("No session found", 401)
    user = DataStore().get_user_by_id(user_id)
    if user is None:
        raise AuthError("User not found", 404)
    if user["is_active"] is False:
        raise AuthError("User is not active", 403)
    return user

# 检查权限
def require_roles(roles: list[str]) -> Callable:
    async def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise AuthError("Permission denied", 403)
        return user
    return dependency