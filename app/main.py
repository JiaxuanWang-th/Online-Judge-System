"""OJ FastAPI application entry."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.repositories.store import DataStore

from app import config
from app.utils.response import error
from app.utils.ids import new_uuid
from app.utils.security import hash_password
from app.utils.time_utils import utc_now_iso
from app.utils.deps import AuthError
from app.routers import auth, users, problems, submissions, logs, admin
# 确保数据相关文件存在
config.ensure_directories()

app = FastAPI(title="Python Summer OJ", version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET, # cookie中存储加密后的 session 数据(这个参数就是密钥)
    session_cookie=config.SESSION_COOKIE_NAME, # 浏览器中 cookie 的名字
    max_age=config.SESSION_MAX_AGE, # 有效期
    same_site="lax", # strict, lax, None
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(problems.router)
app.include_router(submissions.router)
app.include_router(logs.router)
app.include_router(admin.router)


def ensure_default_admin():
    if DataStore().get_user_by_username("admin") is None:
        DataStore().save_user({
            "id": new_uuid(),
            "username": config.DEFAULT_ADMIN_USERNAME,
            "password_hash": hash_password(config.DEFAULT_ADMIN_PASSWORD),
            "role": "admin",
            "is_active": True,
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso()
        })

@app.exception_handler(AuthError)
def auth_handler(_:Request, exc: AuthError):
    return error(exc.message, exc.code)

ensure_default_admin()
frontend_dir = Path(config.FRONTEND_DIR)
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
