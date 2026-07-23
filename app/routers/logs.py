"""Judge log and audit log routes."""

from fastapi import APIRouter, Depends, Query

from app.models.enums import UserRole
from app.repositories.store import DataStore
from app.utils.deps import AuthError, get_current_user, require_roles
from app.utils.response import error, success
from app.utils.sanitize import to_student_log_view, to_teacher_log_view
from app.utils.ids import new_uuid
from app.utils.time_utils import utc_now_iso
from app.utils.pagination import paginate
from app.models.enums import AuditAction, SubmissionStatus

router = APIRouter(prefix="/api", tags=["logs"])

@router.get("/submissions/{submission_id}/logs")
async def get_submission_logs(submission_id: str, user: dict = Depends(get_current_user)):
    case_logs = DataStore().get_case_logs_by_submission(submission_id)
    submission = DataStore().get_submission(submission_id)
    if submission is None:
        return error("submission not found", code=404)
    if submission["status"] == SubmissionStatus.pending.value:
        return success(
            [],
            message="pending submission",
            code=200)
        
    if user["role"] == UserRole.student:
        if submission is not None and submission["user_id"] == user["id"]:
            return success(
            {
                "submission_id": submission_id,
                "status": submission["status"],
                "result": submission.get("result"),
                "score": submission.get("score"),
                "total_time": submission.get("total_time"),
                "cases": to_student_log_view(case_logs),
            },
            message="case logs retrieved successfully", 
            code=200)
        else:
            raise AuthError(f"Permission denied", 403)
    else:
        DataStore().append_audit_log(
            {
                "id": new_uuid(),
                "operator_id": user["id"],
                "action": AuditAction.VIEW_FULL_JUDGE_LOG.value,
                "target_type": "submission",
                "target_id": submission_id,
                "success": True,
                "detail": None,
                "created_at": utc_now_iso(),
            }
        )
        return success(
            {
                "submission_id": submission_id,
                "status": submission["status"],
                "result": submission.get("result"),
                "score": submission.get("score"),
                "total_time": submission.get("total_time"),
                "cases": to_teacher_log_view(case_logs),
            },
            message="case logs retrieved successfully",
            code=200)



@router.get("/logs")
async def get_logs(
    submission_id: str | None = None,
    problem_id: str | None = None,
    user_id: str | None = None,
    result: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_roles([UserRole.teacher, UserRole.admin])),
):
    items = []
    submissions = {s["id"]: s for s in DataStore().list_submissions()}
    for log in DataStore().list_case_logs():
        submission = submissions.get(log["submission_id"])
        if submission_id and log["submission_id"] != submission_id:
            continue
        if problem_id and (not submission or submission["problem_id"] != problem_id):
            continue
        if user_id and (not submission or submission["user_id"] != user_id):
            continue
        if result and log.get("result") != result:
            continue
        created = log.get("created_at") or ""
        if start_time and created < start_time:
            continue
        if end_time and created > end_time:
            continue
        view = to_teacher_log_view([log])[0]
        if submission:
            view["problem_id"] = submission["problem_id"]
            view["user_id"] = submission["user_id"]
        items.append(view)

    items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return success(
        paginate(items, page, page_size),
        message="logs retrieved successfully",
        code=200,
    )


@router.get("/audit-logs")
async def get_audit_logs(
    operator_id: str | None = None,
    action: str | None = None,
    target_id: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_roles([UserRole.admin])),
):
    items = []
    for log in DataStore().list_audit_logs():
        if operator_id and log.get("operator_id") != operator_id:
            continue
        if action and log.get("action") != action:
            continue
        if target_id and log.get("target_id") != target_id:
            continue
        created = log.get("created_at") or ""
        if start_time and created < start_time:
            continue
        if end_time and created > end_time:
            continue
        items.append(log)
    items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return success(
        paginate(items, page, page_size),
        message="audit logs retrieved successfully",
        code=200,
    )