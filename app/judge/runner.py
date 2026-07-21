from app import config
import tempfile
from pathlib import Path
import time
import asyncio
import sys
from app.models.enums import JudgeResult
from app.utils.time_utils import utc_now_iso
from app.utils.sanitize import truncate_text
from app.judge.compare import outputs_equal



async def run_one_case(work_dir, source_path: Path, case, time_limit) -> dict:
    started = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(source_path.name),
            cwd=str(work_dir),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    # SE：评测器出问题
    except Exception as exc:
        return {
            "case_id": case["case_id"],
            "result": JudgeResult.SE.value,
            "score": 0,
            "time_used": 0.0,
            "memory_used": None,
            "exit_code": None,
            "input_data": truncate_text(case.get("input", "")),
            "stdout": "",
            "stderr": "",
            "expected_output": truncate_text(case.get("output", "")),
            "message": truncate_text(f"failed to start process: {exc}"),
            "is_hidden": case.get("is_hidden", False), # 为什么默认 false？
            "created_at": utc_now_iso(),
        }
    # 超时 TLE
    try:
        out_b, err_b = await asyncio.wait_for(
            proc.communicate(input=case.get("input", "").encode("utf-8")),
            timeout=time_limit,
        )
        exit_code = proc.returncode
        time_used = time.perf_counter() - started
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        time_used = time.perf_counter() - started
        return {
            "case_id": case["case_id"],
            "result": JudgeResult.TLE.value,
            "score": 0,
            "time_used": round(time_used, 4),
            "memory_used": None,
            "exit_code": None,
            "input_data": truncate_text(case.get("input", "")),
            "stdout": "",
            "stderr": "",
            "expected_output": truncate_text(case.get("output", "")),
            "message": "time limit exceeded",
            "is_hidden": case.get("is_hidden", False),
            "created_at": utc_now_iso(),
        }
    # RE：（1）结果无法正确解码
    try:
        stdout = out_b.decode("utf-8")
        stderr = err_b.decode("utf-8")
    except UnicodeDecodeError:
        return {
            "case_id": case["case_id"],
            "result": JudgeResult.RE.value,
            "score": 0,
            "time_used": round(time_used, 4),
            "memory_used": None,
            "exit_code": exit_code,
            "input_data": truncate_text(case.get("input", "")),
            "stdout": "",
            "stderr": truncate_text("output is not valid UTF-8"),
            "expected_output": truncate_text(case.get("output", "")),
            "message": "output is not valid UTF-8",
            "is_hidden": case.get("is_hidden", False),
            "created_at": utc_now_iso(),
        }
    expected = case.get("output", "")
    # RE： （2）退出码不为0
    if exit_code != 0:
        return {
            "case_id": case["case_id"],
            "result": JudgeResult.RE.value,
            "score": 0,
            "time_used": round(time_used, 4),
            "memory_used": None,
            "exit_code": exit_code,
            "input_data": truncate_text(case.get("input", "")),
            "stdout": truncate_text(stdout),
            "stderr": truncate_text(stderr),
            "expected_output": truncate_text(expected),
            "message": "runtime error",
            "is_hidden": case.get("is_hidden", False),
            "created_at": utc_now_iso(),
        }
    # AC：退出码为0且答案正确
    if outputs_equal(stdout, expected):
        return {
            "case_id": case["case_id"],
            "result": JudgeResult.AC.value,
            "score": case.get("score", 0),
            "time_used": round(time_used, 4),
            "memory_used": None,
            "exit_code": exit_code,
            "input_data": truncate_text(case.get("input", "")),
            "stdout": truncate_text(stdout),
            "stderr": truncate_text(stderr),
            "expected_output": truncate_text(expected),
            "message": "accepted",
            "is_hidden": case.get("is_hidden", False),
            "created_at": utc_now_iso(),
        }
    # WA：退出码为0但答案不正确
    return {
        "case_id": case["case_id"],
        "result": JudgeResult.WA.value,
        "score": 0,
        "time_used": round(time_used, 4),
        "memory_used": None,
        "exit_code": exit_code,
        "input_data": truncate_text(case.get("input", "")),
        "stdout": truncate_text(stdout),
        "stderr": truncate_text(stderr),
        "expected_output": truncate_text(expected),
        "message": "output does not match expected answer",
        "is_hidden": case.get("is_hidden", False),
        "created_at": utc_now_iso(),
    }

async def judge_submission(submission_id, source_code, problem) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp) / submission_id
        try:
            work_dir.mkdir(parents=True, exist_ok=True)
            source_path = work_dir / "main.py"
            source_path.write_text(source_code, encoding="utf-8")
            time_limit = float(problem.get("time_limit", 1.0))
            case_results: list[dict] = []
            for case in problem.get("test_cases", []):
                result = await run_one_case(work_dir, source_path, case, time_limit)
                result["submission_id"] = submission_id
                case_results.append(result)
                # 首次出现非AC即停止评测
                if result["result"] in {
                    JudgeResult.TLE.value,
                    JudgeResult.RE.value,
                    JudgeResult.SE.value,
                }:
                    break
            score = sum(c["score"] for c in case_results if c["result"] == JudgeResult.AC.value)
            total_time = round(sum(c.get("time_used") or 0 for c in case_results), 4)
            results = [c["result"] for c in case_results]
            if results and all(r == JudgeResult.AC.value for r in results):
                final = JudgeResult.AC.value
            elif JudgeResult.SE.value in results:
                final = JudgeResult.SE.value
            elif JudgeResult.TLE.value in results:
                final = JudgeResult.TLE.value
            elif JudgeResult.RE.value in results:
                final = JudgeResult.RE.value
            else:
                final = JudgeResult.WA.value
            return {
                "result": final,
                "score": score,
                "total_time": total_time,
                "cases": case_results,
            }
        except Exception as exc:
            return {
                "submission_id": submission_id,
                "case_id": "",
                "result": JudgeResult.SE.value,
                "score": 0,
                "time_used": 0.0,
                "memory_used": None,
                "exit_code": None,
                "input_data": "",
                "stdout": "",
                "stderr": "",
                "expected_output": "",
                "message": truncate_text(f"system error: {exc}"),
                "is_hidden": False, # 为什么默认 false？
                "created_at": utc_now_iso(),
            }