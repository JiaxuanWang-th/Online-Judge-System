from app import config
from app.repositories.json_store import JsonStore
from typing import Any, Optional

class DataStore:
    def __init__(self) -> None:
        self.users = JsonStore(config.USERS_FILE, lambda: [])
        self.problems = JsonStore(config.PROBLEMS_FILE, lambda: [])
        self.submissions = JsonStore(config.SUBMISSIONS_FILE, lambda: [])
        self.case_logs = JsonStore(config.CASE_LOGS_FILE, lambda: [])
        self.audit_logs = JsonStore(config.AUDIT_LOGS_FILE, lambda: [])
        self.backups_meta = JsonStore(config.BACKUPS_META_FILE, lambda: [])
    # # # user
    def save_user(self, user: dict[str, Any]):
        # 传参都是对象引用
        def mutator(items: list[dict[str, Any]]) -> dict[str, Any]:
            for idx, existing in enumerate(items):
                if existing["id"] == user["id"]:
                    items[idx] = user
                    return user
            items.append(user)
            return user
        return self.users.update(mutator)

    def list_users(self) -> list[dict[str, Any]]:
        return self.users.read()

    def get_user_by_id(self, user_id: str): # session id
        for user in self.users.read():
            if user["id"] == user_id:
                return user
        return None

    def get_user_by_username(self, user_name: str):
        for user in self.users.read():
            if user["username"] == user_name:
                return user
        return None

    # # # problem
    def list_problems(self) -> list[dict[str, Any]]:
        return self.problems.read()

    def get_problem(self, problem_id: str) -> Optional[dict[str, Any]]:
        for problem in self.problems.read():
            if problem["id"] == problem_id:
                return problem
        return None

    def save_problem(self, problem: dict[str, Any]):
        def mutator(items: list[dict[str, Any]]) -> dict[str, Any]:
            for idx, existing in enumerate(items):
                if existing["id"] == problem["id"]:
                    items[idx] = problem
                    return problem
            items.append(problem)
            return problem
        return self.problems.update(mutator)

    def delete_problem(self, problem_id: str) -> bool:
        def mutator(items: list[dict[str, Any]]) -> Any:
            for problem in items:
                if problem["id"] == problem_id:
                    items.remove(problem)
                    return problem
            return None
        return self.problems.update(mutator)

    # # # submission
    def list_submissions(self) -> list[dict[str, Any]]:
        return self.submissions.read()

    def get_submission(self, submission_id: str) -> Optional[dict[str, Any]]:
        for item in self.submissions.read():
            if item["id"] == submission_id:
                return item
        return None

    def save_submission(self, submission: dict[str, Any]) -> dict[str, Any]:
        def mutator(items: list[dict[str, Any]]) -> dict[str, Any]:
            for idx, existing in enumerate(items):
                if existing["id"] == submission["id"]:
                    items[idx] = submission
                    return submission
            items.append(submission)
            return submission
        return self.submissions.update(mutator)


    # # # case log
    def list_case_logs(self) -> list[dict[str, Any]]:
        return self.case_logs.read()

    def get_case_logs_by_submission(self, submission_id: str) -> list[dict[str, Any]]:
        return [log for log in self.case_logs.read() if log["submission_id"] == submission_id]

    def append_case_log(self, log: dict[str, Any]) -> dict[str, Any]:
        def mutator(items: list[dict[str, Any]]) -> dict[str, Any]:
            items.append(log)
            return log
        return self.case_logs.update(mutator)

    def replace_case_logs(self, submission_id: str, logs: list[dict[str, Any]]) -> dict[str, Any]:
        def mutator(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            # 删除 旧日志
            items[:] = [log for log in items if log["submission_id"] != submission_id]
            items.extend(logs)
            return logs
        return self.case_logs.update(mutator)

    # # # audit log
    def list_audit_logs(self) -> list[dict[str, Any]]:
        return self.audit_logs.read()

    def append_audit_log(self, log: dict[str, Any]) -> dict[str, Any]:
        def mutator(items: list[dict[str, Any]]) -> dict[str, Any]:
            items.append(log)
            return log
        return self.audit_logs.update(mutator)

    # # # backup-meta
    def list_backups_meta(self) -> list[dict[str, Any]]:
        return self.backups_meta.read()

    def save_backup_meta(self, meta: dict[str, Any]) -> dict[str, Any]:
        def mutator(items: list[dict[str, Any]]) -> dict[str, Any]:
            items.append(meta)
            return meta
        return self.backups_meta.update(mutator)

    def get_backup_meta(self, backup_id: str) -> Optional[dict[str, Any]]:
        for meta in self.backups_meta.read():
            if meta["backup_id"] == backup_id:
                return meta
        return None

store = DataStore()