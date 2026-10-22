from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class SubmissionRow(BaseModel):
    id: UUID
    widget_id: UUID
    data: dict
    country: str | None
    city: str | None
    geo_provider: str | None
    created_at: datetime


class WidgetCount(BaseModel):
    widget_id: UUID
    title: str
    count: int


class DayCount(BaseModel):
    day: date
    count: int


class CountryCount(BaseModel):
    country: str
    count: int


class StatsOut(BaseModel):
    days: int
    total: int
    per_widget: list[WidgetCount]
    per_day: list[DayCount]
    per_country: list[CountryCount]