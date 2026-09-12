# Team member: Vinayak Shivam Gupta (@vsh2504)

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail
