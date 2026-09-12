# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateCommentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    body: str = Field(min_length=1)


class User(BaseModel):
    login: str


class Comment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    body: str
    user: User
    created_at: datetime
    html_url: str
