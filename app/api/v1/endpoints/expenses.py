from fastapi import APIRouter, Depends, status

from ....api.deps import get_current_user, get_db_session
from ....models import User
from ....schemas.expense import ExpenseCreate, ExpenseRead
from ....services.expense_service import ExpenseService

router = APIRouter()


@router.get("", response_model=list[ExpenseRead])
async def list_expenses(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = ExpenseService(session)
    expenses = await service.list_expenses(current_user.id, plan_id)
    return [ExpenseRead.from_orm(expense) for expense in expenses]


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def add_expense(
    plan_id: int,
    payload: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = ExpenseService(session)
    expense = await service.add_expense(current_user.id, plan_id, payload)
    return ExpenseRead.from_orm(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    plan_id: int,
    expense_id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = ExpenseService(session)
    await service.delete_expense(current_user.id, plan_id, expense_id)
