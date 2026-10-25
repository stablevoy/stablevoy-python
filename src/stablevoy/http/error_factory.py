from __future__ import annotations

import json

from stablevoy.errors.api_error import ApiError
from stablevoy.errors.authentication_error import AuthenticationError
from stablevoy.errors.maintenance_error import MaintenanceError
from stablevoy.errors.not_found_error import NotFoundError
from stablevoy.errors.problem_issue import ProblemIssue
from stablevoy.errors.rate_limited_error import RateLimitedError
from stablevoy.errors.validation_error import ValidationError


class ErrorFactory:
    """Turns an error answer of the API (an RFC 7807 problem document) into the matching error."""

    def from_problem(self, status: int, body: bytes, retry_after_seconds: int | None) -> ApiError:
        problem = self._parse(body)
        code = problem.get("code")
        code = code if isinstance(code, str) else f"http_{status}"
        detail = problem.get("detail")
        problem_type = problem.get("type")
        error_class: type[ApiError] = ApiError
        if status == 401:
            error_class = AuthenticationError
        elif status == 404:
            error_class = NotFoundError
        elif status == 429:
            error_class = RateLimitedError
        elif status == 503 and code == "maintenance":
            error_class = MaintenanceError
        elif status in (400, 422):
            error_class = ValidationError
        return error_class(
            status=status,
            code=code,
            detail=detail if isinstance(detail, str) else f"The API answered HTTP {status}",
            type=problem_type if isinstance(problem_type, str) else None,
            issues=self._issues(problem.get("issues")),
            retry_after_seconds=retry_after_seconds,
        )

    @staticmethod
    def _parse(body: bytes) -> dict[str, object]:
        try:
            value = json.loads(body)
        except ValueError:
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _issues(value: object) -> tuple[ProblemIssue, ...]:
        if not isinstance(value, list):
            return ()
        return tuple(
            ProblemIssue(issue["path"], issue["message"])
            for issue in value
            if isinstance(issue, dict) and isinstance(issue.get("path"), str) and isinstance(issue.get("message"), str)
        )
