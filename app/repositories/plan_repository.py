from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import TravelPlan


class TravelPlanRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: int) -> list[TravelPlan]:
        result = await self.session.execute(
            select(TravelPlan)
            .options(selectinload(TravelPlan.expenses))
            .where(TravelPlan.owner_id == user_id)
            .order_by(TravelPlan.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_user(self, user_id: int, plan_id: int) -> Optional[TravelPlan]:
        result = await self.session.execute(
            select(TravelPlan)
            .options(selectinload(TravelPlan.expenses))
            .where(
                TravelPlan.id == plan_id,
                TravelPlan.owner_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_for_user(self, user_id: int, data: dict[str, Any]) -> TravelPlan:
        plan = TravelPlan(owner_id=user_id, **data)
        self.session.add(plan)
        await self.session.flush()
        await self.session.refresh(plan)
        return plan

    async def update(self, plan: TravelPlan, data: dict[str, Any]) -> TravelPlan:
        for key, value in data.items():
            setattr(plan, key, value)
        self.session.add(plan)
        await self.session.flush()
        await self.session.refresh(plan)
        return plan

    async def delete(self, plan: TravelPlan) -> None:
        await self.session.delete(plan)
