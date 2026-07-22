from fastapi import APIRouter, Depends, Request
from typing import Any
from datetime import datetime, timezone
from app.models.enums import UserRole, AuditAction
from app.utils.deps import require_roles
from app.utils.response import error, success
from app.repositories.store import DataStore
from app.models.enums import UserRole
from app import config
from pathlib import Path
import shutil, json
from app.utils.time_utils import utc_now_iso
from app.utils.ids import new_uuid

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _data_files()-> list[tuple[str, Path]]:
    return [
        ("users.json", config.USERS_FILE),
        ("problems.json", config.PROBLEMS_FILE),
        ("submissions.json", config.SUBMISSIONS_FILE),
        ("case_logs.json", config.CASE_LOGS_FILE),
        ("audit_logs.json", config.AUDIT_LOGS_FILE),
        ("backups_meta.json", config.BACKUPS_META_FILE),
    ]





def make_backup(operator_id: str) -> dict[str, Any]:
    config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_id = f"backup_{stamp}"
    target = config.BACKUP_DIR / backup_id
    target.mkdir(parents=True, exist_ok=False)

    file_list: list[str] = []
    for name, path in _data_files():
        if path.exists():
            shutil.copy2(path, target / name)
            file_list.append(name)
        else:
            (target / name).write_text("[]", encoding="utf-8") # 文件不存在时默认空[]
            file_list.append(name)

    created_at = utc_now_iso()
    manifest = {
        "backup_id": backup_id,
        "created_at": created_at,
        "storage_type": "json",
        "files": file_list,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    meta = {
        "backup_id": backup_id,
        "created_at": created_at,
        "path": str(target),
    }
    DataStore().save_backup_meta(meta)
    DataStore().append_audit_log(
        {
            "id": new_uuid(),
            "operator_id": operator_id,
            "action": AuditAction.CREATE_BACKUP.value,
            "target_type": "backup",
            "target_id": backup_id,
            "success": True,
            "detail": None,
            "created_at": created_at,
        }
    )
    return meta

def re_backup(backup_id: str, operator_id: str) -> None:
    target = config.BACKUP_DIR / backup_id
    if not target.exists() or not target.is_dir():
        raise LookupError("backup not found")

    manifest_path = target / "manifest.json"
    if not manifest_path.exists():
        raise ValueError("invalid backup: missing manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid backup: corrupted manifest.json") from exc
    
    data_files = _data_files()
    # 检查备份文件是否存在且合法
    for name in [name for name, _ in data_files]:
        file_path = target / name
        if not file_path.exists():
            raise ValueError(f"invalid backup: missing {name}")
        try:
            json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid backup: corrupted {name}") from exc
    
    # Safety copy of current data
    safety_id = f"safety_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    safety_dir = config.BACKUP_DIR / safety_id
    safety_dir.mkdir(parents=True, exist_ok=True)
    for name, path in data_files:
        if path.exists():
            shutil.copy2(path, safety_dir / name)
    
    try:
        for name, path in data_files:
            src = target / name
            if src.exists():
                shutil.copy2(src, path)
        
        DataStore().append_audit_log(
        {
            "id": new_uuid(),
            "operator_id": operator_id,
            "action": AuditAction.RESTORE_BACKUP.value,
            "target_type": "backup",
            "target_id": backup_id,
            "success": True,
            "detail": {"safety_copy": safety_id},
            "created_at": utc_now_iso(),
        }
    )
    except Exception:
        # Restore from safety copy
        for name, path in data_files:
            src = safety_dir / name
            if src.exists():
                shutil.copy2(src, path)
        
        DataStore().append_audit_log(
            {
                "id": new_uuid(),
                "operator_id": operator_id,
                "action": AuditAction.RESTORE_BACKUP.value,
                "target_type": "backup",
                "target_id": backup_id,
                "success": False,
                "detail": {"safety_copy": safety_id},
                "created_at": utc_now_iso(),
            }
        )
        raise
        

    

@router.post("/backups")
async def create_backup(user: dict = Depends(require_roles([UserRole.admin]))):
    try:
        data = make_backup(operator_id=user["id"])
    except Exception as exc:
        return error(f"failed to create backup: {exc}", code=500)
    return success(data, message="backup created", code=201)


@router.get("/backups")
async def list_backups(_: dict = Depends(require_roles([UserRole.admin]))):
    return success({"items": DataStore().list_backups_meta()})


@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    request: Request,
    user: dict = Depends(require_roles([UserRole.admin])),
):
    try:
        re_backup(backup_id, operator_id=user["id"])
    except LookupError:
        return error("backup not found", code=404)
    except ValueError as exc:
        return error(str(exc), code=400)
    except Exception as exc:  # noqa: BLE001
        return error(f"restore failed: {exc}", code=500)
    request.session.clear()
    return success(None, message="backup restored")