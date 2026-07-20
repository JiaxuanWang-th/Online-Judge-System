"""Sanitize user-facing text for logs / responses."""


def truncate_text(text: str, limit: int) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"
