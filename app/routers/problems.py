from fastapi import Depends, APIRouter
from app.models.schemas import ProblemSummary, ProblemCreate, ProblemUpdate
from app.repositories.store import DataStore

from app import config
from app.utils.response import success
from app.utils.deps import AuthError, get_current_user, require_roles

USERS = DataStore().users.read()
router = APIRouter(prefix="/api/problems", tags=["problems"])

# # /api/probelms/*

@router.get("")
async def get_problem_list(_: dict = Depends(get_current_user)): #QUESTION: get_current_user不用传参？
    problems = DataStore().list_problems()
    problem_summaries = [ProblemSummary(
        id = problem["id"],
        title = problem["title"],
        time_limit = problem["time_limit"],
        memory_limit = problem["memory_limit"],
        difficulty = problem["difficulty"],
        tags = problem["tags"]
    ).model_dump(mode="json") for problem in problems]
    return success(problem_summaries, message="get problem list successfully", code=200)

@router.get("/{problem_id}")
async def get_problem(problem_id: str, user: dict = Depends(get_current_user)):
    problem = DataStore().get_problem(problem_id)
    if problem is None:
        raise AuthError("Problem not found", 404)
    get_problem = {}
    if user["role"] == "student":
        get_problem = {
            "id": problem["id"],
            "title": problem["title"],
            "description": problem["description"],
            "input_description": problem["input_description"],
            "output_description": problem["output_description"],
            "samples": problem["samples"],
            "constraints": problem["constraints"],
            "time_limit": problem["time_limit"],
            "memory_limit": problem["memory_limit"],
            "difficulty": problem["difficulty"],
            "tags": problem["tags"]
        }
    else:
        testcases = [
        {
            "case_id": testcase["case_id"],
            "input": testcase["input"],
            "output": testcase["output"],
            "score": testcase["score"],
            "is_hidden": testcase["is_hidden"]
        } 
        for testcase in problem["test_cases"]
    ]
        get_problem = {
            "id": problem["id"],
            "title": problem["title"],
            "description": problem["description"],
            "input_description": problem["input_description"],
            "output_description": problem["output_description"],
            "samples": problem["samples"],
            "constraints": problem["constraints"],
            "time_limit": problem["time_limit"],
            "memory_limit": problem["memory_limit"],
            "difficulty": problem["difficulty"],
            "tags": problem["tags"],
            "test_cases": testcases
        }
    return success(get_problem, message="get problem successfully", code=200)


@router.post("")
async def create_problem(body: ProblemCreate, user: dict = Depends(require_roles(["admin", "teacher"]))):
    problem_id = body.id
    problem = DataStore().get_problem(problem_id)
    if problem is not None:
        raise AuthError("Problem already exists", 409)
    new_problem = body.model_dump(mode="json")
    return success(DataStore().save_problem(new_problem), message="create problem successfully", code=201)



@router.put("/{problem_id}")
async def update_problem(problem_id: str, body: ProblemUpdate, user: dict = Depends(require_roles(["admin", "teacher"]))):
    problem = DataStore().get_problem(problem_id)
    if problem is None:
        raise AuthError("Problem not found", 404)
    problem = {}
    new_problem = body.model_dump(mode="json")
    problem["id"] = problem_id
    problem["title"] = new_problem["title"] if new_problem["title"] is not None else problem["title"]
    problem["description"] = new_problem["description"] if new_problem["description"] is not None else problem["description"]
    problem["input_description"] = new_problem["input_description"] if new_problem["input_description"] is not None else problem["input_description"]
    problem["output_description"] = new_problem["output_description"] if new_problem["output_description"] is not None else problem["output_description"]
    problem["samples"] = new_problem["samples"] if new_problem["samples"] is not None else problem["samples"].model_dump(mode="json")
    problem["constraints"] = new_problem["constraints"] if new_problem["constraints"] is not None else problem["constraints"]
    problem["time_limit"] = new_problem["time_limit"] if new_problem["time_limit"] is not None else problem["time_limit"]
    problem["memory_limit"] = new_problem["memory_limit"] if new_problem["memory_limit"] is not None else problem["memory_limit"]
    problem["difficulty"] = new_problem["difficulty"] if new_problem["difficulty"] is not None else problem["difficulty"]
    problem["tags"] = new_problem["tags"] if new_problem["tags"] is not None else problem["tags"]
    problem["test_cases"] = new_problem["test_cases"] if new_problem["test_cases"] is not None else problem["test_cases"]
    return success(DataStore().save_problem(problem), message="update problem successfully", code=200)

@router.delete("/{problem_id}")
async def delete_problem(problem_id: str, user: dict = Depends(require_roles(["admin", "teacher"]))):
    problem = DataStore().get_problem(problem_id)
    if problem is None:
        raise AuthError("Problem not found", 404)
    return success(DataStore().delete_problem(problem_id), message="delete problem successfully", code=200)