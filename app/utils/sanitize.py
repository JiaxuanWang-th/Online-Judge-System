"""Sanitize user-facing text for logs / responses."""

import app.config as config

def truncate_text(text: str, limit: int=config.LOG_TEXT_LIMIT) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"
