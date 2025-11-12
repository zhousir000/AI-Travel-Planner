from datetime import datetime

from pydantic import BaseModel, Field


class ExpenseBase(BaseModel):
    category: str = Field(examples=["food", "transport"])
    amount: float = Field(gt=0)
    currency: str = "CNY"
    note: str | None = None


class ExpenseCreate(ExpenseBase):
    incurred_at: datetime | None = None


class ExpenseRead(ExpenseBase):
    id: int
    plan_id: int
    incurred_at: datetime

    model_config = {"from_attributes": True}
