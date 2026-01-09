"""
Pydantic data models for API requests and responses.
"""

from typing import Any

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint."""

    success: bool
    message: str
    table_name: str | None = None
    row_count: int | None = None
    schema: dict[str, str] | None = None
    sample_data: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    """Response model for errors."""

    success: bool = False
    error: str
