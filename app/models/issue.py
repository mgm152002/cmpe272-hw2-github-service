# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Label(BaseModel):
    name: str


class CreateIssueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=256)
    body: str | None = None
    labels: list[str] = Field(default_factory=list)


class UpdateIssueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=256)
    body: str | None = None
    state: Literal["open", "closed"] | None = None


class Issue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    number: int
    html_url: str
    state: Literal["open", "closed"]
    title: str
    body: str | None = None
    labels: list[Label] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
