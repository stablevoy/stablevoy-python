from __future__ import annotations

from stablevoy.errors.problem_issue import ProblemIssue
from stablevoy.errors.stablevoy_error import StablevoyError


class ApiError(StablevoyError):
    """
    The API answered with an error: an RFC 7807 problem document with a stable code, a readable detail and a link to the
    code's entry in the error catalog (https://stablevoy.com/docs/api/errors/).
    """

    def __init__(
        self,
        *,
        status: int,
        code: str,
        detail: str,
        type: str | None,
        issues: tuple[ProblemIssue, ...],
        retry_after_seconds: int | None,
    ) -> None:
        super().__init__(f"{detail} (HTTP {status}, {code})")
        self.status = status
        self.code = code
        self.detail = detail
        self.type = type
        self.issues = issues
        self.retry_after_seconds = retry_after_seconds
