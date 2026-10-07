from fastapi import HTTPException, status


class DomainException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFoundError(DomainException):
    def __init__(self, resource: str, identifier: str | int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id '{identifier}' not found."
        )


class ConcurrencyConflictError(DomainException):
    def __init__(self, current_version: int, provided_version: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Optimistic Concurrency Conflict: Board has version {current_version}, but client submitted version {provided_version}. Please refresh canvas state before saving."
        )


class PermissionDeniedError(DomainException):
    def __init__(self, action: str = "perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied to {action}."
        )


class ValidationError(DomainException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
