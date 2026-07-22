"""Shared enums for the OJ domain."""

from enum import Enum


class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class SubmissionStatus(str, Enum):
    pending = "pending"
    running = "running"
    finished = "finished"
    failed = "failed"


class JudgeResult(str, Enum):
    AC = "AC"
    WA = "WA"
    RE = "RE"
    TLE = "TLE"
    SE = "SE"

class AuditAction(str, Enum):
    VIEW_FULL_JUDGE_LOG = "VIEW_FULL_JUDGE_LOG"
    REJUDGE_SUBMISSION = "REJUDGE_SUBMISSION"
    CREATE_BACKUP = "CREATE_BACKUP"
    RESTORE_BACKUP = "RESTORE_BACKUP"
    SIMILARITY_CHECK = "SIMILARITY_CHECK"
    UPDATE_USER_ROLE = "UPDATE_USER_ROLE"
    DISABLE_USER = "DISABLE_USER"