"""OJ FastAPI application entry."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app import config
from app.utils.response import success

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


@app.get("/api/health")
async def health():
    return success(data={"status": "ok"})


# Routers will be included here in later stages, e.g.:
# from app.routers import auth, problems, submissions, logs, backup
# app.include_router(auth.router, prefix="/api")
# ...

frontend_dir = Path(config.FRONTEND_DIR)
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
