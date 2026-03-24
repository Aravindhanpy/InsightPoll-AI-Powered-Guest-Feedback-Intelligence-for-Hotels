"""
models.py
---------
Two layers live here:

1. DB Table Models (SQLModel)
   PollDB, ResponseDB — define the actual SQLite columns.
   ResponseDB includes created_at for sentiment trend chart.

2. API Schemas (Pydantic BaseModel)
   PollCreate, ResponseCreate — what the API accepts as request bodies.
"""

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, Column
from pydantic import BaseModel, field_validator
from typing import List, Optional


# ── Database table models ──────────────────────────────────────────────────────

class PollDB(SQLModel, table=True):
    __tablename__ = "polls"

    id:       int       = Field(primary_key=True)
    question: str
    options:  List[str] = Field(sa_column=Column(JSON), default=[])

    responses: List["ResponseDB"] = Relationship(back_populates="poll")


class ResponseDB(SQLModel, table=True):
    __tablename__ = "responses"

    id:              Optional[int]      = Field(default=None, primary_key=True)
    poll_id:         int                = Field(foreign_key="polls.id")
    selected_option: str
    text_feedback:   Optional[str]      = None
    created_at:      Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    poll: Optional[PollDB] = Relationship(back_populates="responses")


# ── API request schemas ────────────────────────────────────────────────────────

class PollCreate(BaseModel):
    id:       int
    question: str
    options:  List[str]

    @field_validator("options")
    @classmethod
    def no_duplicate_options(cls, v: List[str]) -> List[str]:
        if len(v) != len(set(v)):
            raise ValueError("Poll options must be unique")
        return v

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class ResponseCreate(BaseModel):
    poll_id:         int
    selected_option: str
    text_feedback:   Optional[str] = None
