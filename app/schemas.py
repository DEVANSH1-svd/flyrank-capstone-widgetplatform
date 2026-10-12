from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class FormField(BaseModel):
    name: str = Field(min_length=1, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    label: str = Field(min_length=1, max_length=100)
    type: Literal["text", "email", "textarea"] = "text"
    required: bool = False


class WidgetIn(BaseModel):
    """Body for creating or fully replacing a widget."""

    type: Literal["signup_form", "contact_form"]
    title: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    fields: list[FormField] = Field(min_length=1, max_length=10)
    button_text: str = Field(min_length=1, max_length=40)
    is_active: bool = True


class WidgetOut(BaseModel):
    id: UUID
    public_id: str
    type: str
    title: str
    description: str | None
    fields: list[FormField]
    button_text: str
    config_version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SnippetOut(BaseModel):
    snippet: str


class SubmissionIn(BaseModel):
    """Public, untrusted input. Everything is validated before use."""

    widget_id: str = Field(min_length=1, max_length=64)  # the widget's public id
    data: dict[str, str]
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)
    website: str = Field(default="", max_length=500)  # honeypot: humans leave it empty


class SubmissionOut(BaseModel):
    id: UUID
    status: str
