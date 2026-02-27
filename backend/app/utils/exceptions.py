"""Custom exceptions used across service/controller layers."""


class AIServiceError(Exception):
    """Raised when AI provider interaction fails or returns invalid output."""

    pass


class DatabaseError(Exception):
    """Raised when persistence operations fail."""

    pass
