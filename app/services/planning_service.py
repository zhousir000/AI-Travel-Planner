import json
from datetime import date, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TravelPlan, User
from ..repositories.plan_repository import TravelPlanRepository
from ..schemas.plan import PlanGenerationRequest
from .llm_client import LLMClient, LLMClientError


class PlanningService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.plan_repo = TravelPlanRepository(session)

    async def generate_plan(self, user: User, request: PlanGenerationRequest) -> TravelPlan:
        overrides = {
            "provider": request.llm_provider,
            "api_key": request.llm_api_key,
            "endpoint": request.llm_endpoint,
            "model": request.llm_model,
        }
        llm_client = LLMClient(
            **{key: value for key, value in overrides.items() if value}  # pass only explicitly provided overrides
        )
        try:
            llm_plan = await llm_client.generate_plan(request)
        except LLMClientError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        plan_data = self._build_plan_data(user, request, llm_plan)
        plan = await self.plan_repo.create_for_user(user.id, plan_data)
        await self.session.commit()
        return plan

    async def list_plans(self, user: User) -> list[TravelPlan]:
        return await self.plan_repo.list_for_user(user.id)

    async def get_plan(self, user: User, plan_id: int) -> TravelPlan:
        plan = await self.plan_repo.get_for_user(user.id, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return plan

    async def update_plan(self, user: User, plan_id: int, data: dict[str, Any]) -> TravelPlan:
        plan = await self.get_plan(user, plan_id)
        updated = await self.plan_repo.update(plan, data)
        await self.session.commit()
        return updated

    async def delete_plan(self, user: User, plan_id: int) -> None:
        plan = await self.get_plan(user, plan_id)
        await self.plan_repo.delete(plan)
        await self.session.commit()

    def _build_plan_data(
        self,
        user: User,
        request: PlanGenerationRequest,
        llm_plan: dict[str, Any],
    ) -> dict[str, Any]:
        title = llm_plan.get("title") or f"{request.destination} Adventure"
        days = llm_plan.get("days", [])
        start_date = request.start_date
        end_date = request.end_date
        if start_date and days:
            for idx, day in enumerate(days):
                if isinstance(day, dict):
                    day["date"] = (start_date + timedelta(days=idx)).isoformat()
            if not end_date:
                end_date = start_date + timedelta(days=len(days) - 1)
        if not start_date and days:
            first_day_date = days[0].get("date")
            if first_day_date:
                start_date = date.fromisoformat(first_day_date)
        if not end_date and start_date and days:
            end_day_date = days[-1].get("date")
            if end_day_date:
                end_date = date.fromisoformat(end_day_date)
        duration = request.duration_days or len(days) or None
        budget_block = llm_plan.get("budget") or {}
        itinerary_payload = {
            "days": days,
            "tips": llm_plan.get("tips", []),
            "summary": llm_plan.get("summary"),
        }
        preferences_payload = {
            "travel_style": request.travel_style,
            "interests": request.interests,
            "traveling_with_children": request.traveling_with_children,
            "voice_transcript": request.voice_transcript,
        }
        return {
            "title": title,
            "destination": request.destination,
            "start_date": start_date,
            "end_date": end_date,
            "duration_days": duration,
            "travelers": request.travelers,
            "budget_amount": budget_block.get("total") or request.budget_amount,
            "currency": budget_block.get("currency") or request.currency,
            "preferences": preferences_payload,
            "itinerary": itinerary_payload,
            "budget_breakdown": {"summary": budget_block},
            "notes": request.notes,
            "raw_plan_text": json.dumps(llm_plan, ensure_ascii=False),
        }
