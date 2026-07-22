"""Sanitize user-facing text for logs / responses."""

import app.config as config
from typing import Any
def truncate_text(text: str, limit: int=config.LOG_TEXT_LIMIT) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"


import re
def satinize_paths(text: str) -> str:
    text = re.sub(r"[A-Za-z]:\\[^\s]+", "<submission>/...", text)  # Windows
    text = re.sub(r"(?:/|\\)(?:[^\s/\\]+[/\\])+temp[/\\][^\s]+", "<submission>/main.py", text)
    return text

# QUESTION: 如何实现“脱敏”？
def to_student_log_view(log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cases = [
        {
            "case_id": case["case_id"],
            "result": case["result"],
            "score": case["score"],
            "time_used": case["time_used"],
            "memory_used": case["memory_used"],
            "stderr": satinize_paths(truncate_text(case["stderr"])),
            "message": truncate_text(case["message"]),
        }
        if case["is_hidden"] == True else
        {
            "case_id": case["case_id"],
            "result": case["result"],
            "score": case["score"],
            "time_used": case["time_used"],
            "memory_used": case["memory_used"],
            "stderr": satinize_paths(truncate_text(case["stderr"])),
            "message": truncate_text(case["message"]),
            "stdout": truncate_text(case["stdout"]),
            "expected_output": truncate_text(case["expected_output"]),
        }
        for case in log
    ]
    return cases



def to_teacher_log_view(log: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return log