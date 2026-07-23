import asyncio
from typing import Any
from fastapi import Depends, APIRouter, Query
from app.models.schemas import SubmissionCreate
from app.repositories.store import DataStore
from app.utils.time_utils import utc_now_iso
from app.models.enums import JudgeResult, AuditAction, UserRole, SubmissionStatus
from app import config
from app.utils.response import success
from app.utils.deps import AuthError, get_current_user, require_roles
from app.utils.ids import new_uuid
from app.utils.pagination import paginate
from app.judge.runner import judge_submission

USERS = DataStore().users.read()
router = APIRouter(prefix="/api/submissions", tags=["submissions"])

async def run_test(submission, problem, content):
    running_content = content.copy()
    running_content["status"] = SubmissionStatus.running.value
    running_content["started_at"] = utc_now_iso()
    submission = DataStore().save_submission(running_content)
    results = await judge_submission(submission["id"], submission["source_code"], problem)
    running_content["finished_at"] = utc_now_iso()
    running_content["result"] = results["result"]
    running_content["status"] = SubmissionStatus.failed.value if results["result"] == JudgeResult.SE.value else SubmissionStatus.finished.value
    running_content["score"] = results["score"]
    running_content["total_time"] = results["total_time"]
    submission = DataStore().save_submission(running_content)
    DataStore().replace_case_logs(submission["id"], results["cases"])
    return running_content



@router.post("")
async def create_submission(body: SubmissionCreate, user: dict = Depends(get_current_user)):
    problem_id = body.problem_id
    problem = DataStore().get_problem(problem_id)
    if problem is None:
        raise AuthError("Problem not found", 404)
    content = {
        "id": new_uuid(),
        "user_id": user["id"],
        "status": SubmissionStatus.pending.value,
        "result": None,
        "score": 0,
        "total_time": None,
        "created_at": utc_now_iso(),
        "started_at": None,
        "finished_at": None,
        "language": body.language,
        "source_code": body.source_code,
        "problem_id": problem_id,
    }
    submission = DataStore().save_submission(content)
    asyncio.create_task(run_test(submission, problem, content))
    return success(content, message="submission created successfully", code=202)


@router.get("/{submission_id}")
async def get_submission(submission_id: str, user: dict = Depends(get_current_user)):
    submission = DataStore().get_submission(submission_id)
    if submission == None:
        raise AuthError(f"Submission {submission_id} not found", 404)
    else:
        # 学生访问：必须确保访问的submission_id与user_id绑定
        if user["role"] == UserRole.student:
            if user["id"] != submission["user_id"]:
                raise AuthError(f"Permission denied", 403)
            else:
                return success(submission, message=f"submission {submission_id} retrieved successfully", code=200)
        else:
            return success(submission, message=f"submission {submission_id} retrieved successfully", code=200)


@router.get("")
async def list_submissions(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    if user["role"] == UserRole.student:
        submissions = DataStore().list_submissions()
        submission_list = [submission for submission in submissions if submission["user_id"] == user["id"]]
    else:
        submission_list = DataStore().list_submissions()
    return success(
        paginate(submission_list, page, page_size),
        message="submissions retrieved successfully",
        code=200,
    )


@router.post("/{submission_id}/rejudge")
async def rejudge_submission(submission_id: str, user: dict = Depends(get_current_user)):
    if user["role"] == UserRole.student:
        raise AuthError(f"Permission denied", 403)
    submission = DataStore().get_submission(submission_id)
    if submission == None:
        raise AuthError(f"Submission {submission_id} not found", 404)
    if submission["status"] == SubmissionStatus.finished.value or submission["status"] == SubmissionStatus.failed.value:
        problem = DataStore().get_problem(submission["problem_id"])
        if problem is None:
            raise AuthError("Problem not found", 404)
        content = {
            "id": submission["id"],
            "user_id": submission["user_id"],
            "status": SubmissionStatus.pending.value,
            "result": None,
            "score": 0,
            "total_time": None,
            "created_at": utc_now_iso(),
            "started_at": None,
            "finished_at": None,
            "language": submission["language"],
            "source_code": submission["source_code"],
            "problem_id": submission["problem_id"],
        }
        submission = DataStore().save_submission(content)
        asyncio.create_task(run_test(submission, problem, content))
        DataStore().append_audit_log(
            {
                "id": new_uuid(),
                "operator_id": user["id"],
                "action": AuditAction.REJUDGE_SUBMISSION.value,
                "target_type": "submission",
                "target_id": submission_id,
                "success": True,
                "created_at": utc_now_iso(),
            }
        )
        return success(content, message="submission created successfully", code=202)
    else:
        raise AuthError(f"Submission {submission_id} is not finished or failed", 409)
