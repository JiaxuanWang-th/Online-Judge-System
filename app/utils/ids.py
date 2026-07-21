"""ID generators."""
from uuid import uuid4

# 生成随机唯一 ID
def new_uuid() -> str:
    return str(uuid4())
