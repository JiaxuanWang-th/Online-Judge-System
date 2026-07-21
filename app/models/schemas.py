"""Pydantic request/response schemas — fill in during later stages."""

import re
from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.enums import UserRole, Difficulty, SubmissionStatus
from typing import Optional


class SampleIO(BaseModel):
    input: str
    output: str
    explanation: Optional[str] = None

class TestCase(BaseModel):
    case_id: str = Field(min_length=1)
    input: str
    output: str
    score: int = Field(ge=0)
    is_hidden: bool = False


class ProblemBase(BaseModel):
    id : str
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    input_description: str = Field(min_length=1)
    output_description: str = Field(min_length=1)
    samples: list[SampleIO] = Field(min_length=1)
    constraints: str = ""
    time_limit: float = Field(gt=0)
    memory_limit: int = Field(gt=0)
    difficulty: Difficulty = Field(default=Difficulty.EASY)
    tags: list[str] = Field(default_factory=list) # 避免共用一个 list 实例
    test_cases: list[TestCase] = Field(min_length=1)

    # 题目 id 合法性检查，特定字段自定义检查
    @field_validator("id")
    @classmethod
    def validate_id(cls, value: str) -> str:
        if not re.match(r"^[A-Za-z0-9_-]{1,32}$", value):
            raise ValueError("id must be 1-32 chars of letters, digits, underscore or hyphen")
        return value

    # 跨字段检查
    @model_validator(mode="after")
    def validate_test_cases(self) -> "ProblemBase":
        case_ids = [c.case_id for c in self.test_cases]
        # case id 不重复
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case_id must be unique within a problem")
        # 总分100
        total_score = sum(c.score for c in self.test_cases)
        if total_score != 100:
            raise ValueError("sum of test case scores must equal 100")
        return self

class ProblemCreate(ProblemBase):
    pass

class ProblemUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    input_description: str = Field(min_length=1)
    output_description: str = Field(min_length=1)
    samples: list[SampleIO] = Field(min_length=1)
    constraints: str = ""
    time_limit: float = Field(gt=0)
    memory_limit: int = Field(gt=0)
    difficulty: Difficulty = Field(default=Difficulty.EASY)
    tags: list[str] = Field(default_factory=list) # 避免共用一个 list 实例
    test_cases: list[TestCase] = Field(min_length=1)

    # 跨字段检查
    @model_validator(mode="after")
    def validate_test_cases(self) -> "ProblemUpdate":
        case_ids = [c.case_id for c in self.test_cases]
        # case id 不重复
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case_id must be unique within a problem")
        # 总分100
        total_score = sum(c.score for c in self.test_cases)
        if total_score != 100:
            raise ValueError("sum of test case scores must equal 100")
        return self

# 题目列表中展示题目的简要信息
class ProblemSummary(BaseModel):
    id : str
    title: str = Field(min_length=1, max_length=100)
    time_limit: float = Field(gt=0)
    memory_limit: int = Field(gt=0)
    difficulty: Difficulty = Field(default=Difficulty.EASY)
    tags: list[str] = Field(default_factory=list) # 避免共用一个 list 实例



# Auth & User

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    username: str
    password: str

class UserUpdateRequest(BaseModel):
    role: Optional[UserRole] = None # role 可传可不传
    is_active: Optional[bool] = None

class UserPublic(BaseModel):
    id: str
    username: str
    role: UserRole
    is_active: bool
    created_at: str
    updated_at: str


# Submission

class SubmissionCreate(BaseModel):
    problem_id: str
    language: str = "python"
    source_code: str = Field(min_length=1)

    # 只支持python
    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        if value != "python":
            raise ValueError("only python is supported")
        return value
    # 代码内存必须<=64kb
    @field_validator("source_code")
    @classmethod
    def validate_source_size(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 64 * 1024:
            raise ValueError("source code exceeds 64 KiB")
        return value