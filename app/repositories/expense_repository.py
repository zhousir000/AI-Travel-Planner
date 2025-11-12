from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Expense


class ExpenseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_plan(self, plan_id: int) -> list[Expense]:
        result = await self.session.execute(
            select(Expense).where(Expense.plan_id == plan_id).order_by(Expense.incurred_at.desc())
        )
        return list(result.scalars().all())

    async def create_for_plan(
        self,
        plan_id: int,
        *,
        category: str,
        amount: float,
        currency: str,
        note: str | None,
        incurred_at: datetime | None,
    ) -> Expense:
        expense = Expense(plan_id=plan_id, category=category, amount=amount, currency=currency, note=note, incurred_at=incurred_at)
        self.session.add(expense)
        await self.session.flush()
        await self.session.refresh(expense)
        return expense

    async def get(self, expense_id: int, plan_id: int) -> Optional[Expense]:
        result = await self.session.execute(
            select(Expense).where(Expense.id == expense_id, Expense.plan_id == plan_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, expense: Expense) -> None:
        await self.session.delete(expense)
