# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.clients.github_client import GitHubClient
from app.dependencies import get_github_client
from app.models.comment import Comment, CreateCommentRequest
from app.models.issue import CreateIssueRequest, Issue, UpdateIssueRequest

router = APIRouter(prefix="/issues", tags=["Issues"])
Client = Annotated[GitHubClient, Depends(get_github_client)]
IssueNumber = Annotated[int, Path(ge=1)]


@router.post("", response_model=Issue, status_code=status.HTTP_201_CREATED)
async def create_issue(payload: CreateIssueRequest, response: Response, client: Client) -> Issue:
    github_response = await client.request("POST", "/issues", json=payload.model_dump(exclude_none=True))
    issue = Issue.model_validate(github_response.json())
    response.headers["Location"] = f"/issues/{issue.number}"
    return issue


@router.get("", response_model=list[Issue])
async def list_issues(
    response: Response,
    client: Client,
    state: Literal["open", "closed", "all"] = "open",
    labels: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> list[Issue]:
    upstream = await client.request(
        "GET", "/issues", params={"state": state, "labels": labels, "page": page, "per_page": per_page}
    )
    if link := upstream.headers.get("link"):
        response.headers["Link"] = link
    return [Issue.model_validate(item) for item in upstream.json() if "pull_request" not in item]


@router.get("/{number}", response_model=Issue)
async def get_issue(number: IssueNumber, client: Client) -> Issue:
    response = await client.request("GET", f"/issues/{number}")
    return Issue.model_validate(response.json())


@router.patch("/{number}", response_model=Issue)
async def update_issue(
    number: IssueNumber, payload: UpdateIssueRequest, client: Client
) -> Issue:
    response = await client.request(
        "PATCH", f"/issues/{number}", json=payload.model_dump(exclude_none=True)
    )
    return Issue.model_validate(response.json())


@router.post("/{number}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
async def create_comment(
    number: IssueNumber, payload: CreateCommentRequest, client: Client
) -> Comment:
    response = await client.request("POST", f"/issues/{number}/comments", json=payload.model_dump())
    return Comment.model_validate(response.json())


@router.get("/{number}/comments", response_model=list[Comment])
async def list_comments(
    number: IssueNumber,
    response: Response,
    client: Client,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
) -> list[Comment]:
    upstream = await client.request(
        "GET",
        f"/issues/{number}/comments",
        params={"page": page, "per_page": per_page},
    )
    if link := upstream.headers.get("link"):
        response.headers["Link"] = link
    return [Comment.model_validate(item) for item in upstream.json()]
