from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, Field, validator

from .expense import ExpenseRead


class Preference(BaseModel):
    key: str
    value: Any


class ItineraryActivity(BaseModel):
    time: str | None = None
    title: str
    description: str | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    estimated_cost: float | None = None


class ItineraryDay(BaseModel):
    day_index: int
    date: dt.date | None = None
    headline: str | None = None
    activities: list[ItineraryActivity] = Field(default_factory=list)


class BudgetLine(BaseModel):
    category: str
    amount: float
    currency: str = "CNY"
    notes: str | None = None


class PlanIntent(BaseModel):
    destination: str
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    duration_days: int | None = None
    budget_amount: float | None = None
    currency: str = "CNY"
    travelers: int | None = None
    travel_style: list[str] = Field(default_factory=list)
    traveling_with_children: bool | None = None
    interests: list[str] = Field(default_factory=list)
    custom_request: str | None = None

    @validator("travel_style", "interests", pre=True)
    def ensure_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [s.strip() for s in value.split(",") if s.strip()]
        return list(value)


class PlanGenerationRequest(PlanIntent):
    voice_transcript: str | None = None
    notes: str | None = None
    llm_provider: str | None = Field(
        default=None, description="Override which LLM provider to use for this generation."
    )
    llm_model: str | None = Field(default=None, description="Optional model override for the selected provider.")
    llm_endpoint: str | None = Field(default=None, description="Optional API endpoint override.")
    llm_api_key: str | None = Field(default=None, description="Optional API key override for the provider.")


class PlanGenerationResponse(BaseModel):
    plan: "TravelPlanRead"


class TravelPlanBase(BaseModel):
    title: str
    destination: str
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    duration_days: int | None = None
    travelers: int | None = None
    budget_amount: float | None = None
    currency: str = "CNY"
    preferences: dict[str, Any] | None = None
    itinerary: dict[str, Any] | None = None
    budget_breakdown: dict[str, Any] | None = None
    notes: str | None = None
    raw_plan_text: str | None = None


class TravelPlanCreate(TravelPlanBase):
    pass


class TravelPlanUpdate(BaseModel):
    title: str | None = None
    start_date: dt.date | None = None
    end_date: dt.date | None = None
    duration_days: int | None = None
    travelers: int | None = None
    budget_amount: float | None = None
    currency: str | None = None
    preferences: dict[str, Any] | None = None
    itinerary: dict[str, Any] | None = None
    budget_breakdown: dict[str, Any] | None = None
    notes: str | None = None


class TravelPlanRead(TravelPlanBase):
    id: int
    owner_id: int
    created_at: dt.datetime
    updated_at: dt.datetime
    expenses: list[ExpenseRead] | None = None

    model_config = {"from_attributes": True}


PlanGenerationResponse.model_rebuild()
