
from typing import Optional, Dict, Any


class APIException(Exception):
    """
    Base exception class for all API errors.
    Provides a consistent structure for error responses.
    
    Usage:
        raise APIException(
            status_code=400,
            message="Invalid input provided",
            error_code="INVALID_INPUT"
        )
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Args:
            status_code: HTTP status code (400, 404, 500, etc.)
            message: User-friendly error message
            error_code: Machine-readable error identifier
            details: Additional error context for debugging
        """
        self.status_code = status_code
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to JSON-serializable dictionary."""
        return {
            "status": "error",
            "status_code": self.status_code,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

# HTTP Status Codes

# 4xx Client Errors
class BadRequestException(APIException):
    """400 - Invalid request format or parameters."""

    def __init__(self, message: str, error_code: str = "BAD_REQUEST", details: Optional[Dict] = None):
        super().__init__(status_code=400, 
                         message=message, error_code=error_code, details=details)


class UnauthorizedException(APIException):
    """401 - Authentication required or failed."""

    def __init__(self, message: str = "Authentication required", error_code: str = "UNAUTHORIZED", details: Optional[Dict] = None):
        super().__init__(status_code=401, 
                         message=message, error_code=error_code, details=details)


class ForbiddenException(APIException):
    """403 - Authenticated but lacks permission."""

    def __init__(self, message: str = "Access forbidden", error_code: str = "FORBIDDEN", details: Optional[Dict] = None):
        super().__init__(status_code=403, 
                         message=message, error_code=error_code, details=details)


class NotFoundException(APIException):
    """404 - Resource not found."""

    def __init__(self, resource: str, identifier: str = "", error_code: str = "NOT_FOUND", details: Optional[Dict] = None):
        message = f"{resource} not found"
        if identifier:
            message += f" (ID: {identifier})"
        super().__init__(status_code=404, 
                         message=message, error_code=error_code, details=details)


class ConflictException(APIException):
    """409 - Resource conflict (e.g., duplicate entry)."""

    def __init__(self, message: str, error_code: str = "CONFLICT", details: Optional[Dict] = None):
        super().__init__(status_code=409, 
                         message=message, error_code=error_code, details=details)


class ValidationException(APIException):
    """422 - Validation error."""

    def __init__(self, field: str, reason: str, error_code: str = "VALIDATION_ERROR", details: Optional[Dict] = None):
        message = f"Validation failed for field '{field}': {reason}"
        super().__init__(status_code=422, 
                         message=message, error_code=error_code, details=details)


class InvalidObjectIdException(APIException):
    """400 - Invalid MongoDB ObjectId format."""

    def __init__(self, field: str, value: str, error_code: str = "INVALID_OBJECT_ID"):
        message = f"Invalid ObjectId format for field '{field}': {value}"
        super().__init__(
            status_code=400,
            message=message,
            error_code=error_code,
            details={"field": field, "value": value},
        )


# 5xx Server Errors
class InternalServerException(APIException):
    """500 - Internal server error."""

    def __init__(self, message: str = "Internal server error", error_code: str = "INTERNAL_ERROR", details: Optional[Dict] = None):
        super().__init__(status_code=500, 
                         message=message, error_code=error_code, details=details)


class DatabaseException(APIException):
    """500 - Database operation failed."""

    def __init__(self, operation: str, error_code: str = "DATABASE_ERROR", details: Optional[Dict] = None):
        message = f"Database error during {operation}"
        super().__init__(status_code=500, 
                         message=message, error_code=error_code, details=details)


class ExternalServiceException(APIException):
    """502 - External service unavailable."""

    def __init__(self, service: str, error_code: str = "SERVICE_UNAVAILABLE", details: Optional[Dict] = None):
        message = f"External service '{service}' is unavailable"
        super().__init__(status_code=502, 
                         message=message, error_code=error_code, details=details)
