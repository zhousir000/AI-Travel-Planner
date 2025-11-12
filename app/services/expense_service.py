from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.expense_repository import ExpenseRepository
from ..repositories.plan_repository import TravelPlanRepository
from ..schemas.expense import ExpenseCreate


class ExpenseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ExpenseRepository(session)
        self.plan_repo = TravelPlanRepository(session)

    async def list_expenses(self, user_id: int, plan_id: int):
        plan = await self.plan_repo.get_for_user(user_id, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        return await self.repo.list_for_plan(plan.id)

    async def add_expense(self, user_id: int, plan_id: int, payload: ExpenseCreate):
        plan = await self.plan_repo.get_for_user(user_id, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        incurred_at = payload.incurred_at or datetime.now(timezone.utc)
        expense = await self.repo.create_for_plan(
            plan.id,
            category=payload.category,
            amount=payload.amount,
            currency=payload.currency,
            note=payload.note,
            incurred_at=incurred_at,
        )
        await self.session.commit()
        return expense

    async def delete_expense(self, user_id: int, plan_id: int, expense_id: int) -> None:
        plan = await self.plan_repo.get_for_user(user_id, plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
        expense = await self.repo.get(expense_id, plan.id)
        if not expense:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
        await self.repo.delete(expense)
        await self.session.commit()
