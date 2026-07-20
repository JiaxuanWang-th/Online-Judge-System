import json, os
from pathlib import Path
from typing import Any, Callable # Any是Python的通配符类型，表示任何类型
import threading

class JsonStoreError(Exception):
    pass

class JsonStore:
    def __init__(self, path: Path, default_json: Callable[[], Any]):
        self.path = path
        self.default_json = default_json
        self._lock = threading.RLock()

    # 原子写入
    def _atomic_write(self, data: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # 写入临时文件
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # 文件更新
        os.replace(tmp_path, self.path)

    # 读
    def read(self) -> Any:
        with self._lock:
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                data = self.default_json() # 按需生成 [] or {}
                self._atomic_write(data)
                return data
            except json.JSONDecodeError as e:
                # 自定义异常`JsonStoreError` （只是换了个名字）
                raise JsonStoreError(f"corrupted data file: {self.path.name}") from e
    
    # 写
    def write(self, data: Any) -> None:
        with self._lock:
            self._atomic_write(data)

    # 数据更新全过程
    def update(self, mutator: Callable[[Any], Any]) -> Any:
        with self._lock:
            data = self.read()
            result = mutator(data) # 修改数据
            self.write(data)
            return result # 返回更新部分的数据
