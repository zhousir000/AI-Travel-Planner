from typing import Sequence

from fastapi import APIRouter, Depends, status

from ....api.deps import get_current_user, get_db_session
from ....models import TravelPlan, User
from ....schemas.plan import PlanGenerationRequest, PlanGenerationResponse, TravelPlanRead, TravelPlanUpdate
from ....services.planning_service import PlanningService

router = APIRouter()


def serialize_plan(plan: TravelPlan) -> TravelPlanRead:
    return TravelPlanRead.from_orm(plan)


@router.get("", response_model=list[TravelPlanRead])
async def list_plans(
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = PlanningService(session)
    plans = await service.list_plans(current_user)
    return [serialize_plan(plan) for plan in plans]


@router.post("/generate", response_model=PlanGenerationResponse, status_code=status.HTTP_201_CREATED)
async def generate_plan(
    payload: PlanGenerationRequest,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = PlanningService(session)
    plan = await service.generate_plan(current_user, payload)
    return PlanGenerationResponse(plan=serialize_plan(plan))


@router.get("/{plan_id}", response_model=TravelPlanRead)
async def get_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = PlanningService(session)
    plan = await service.get_plan(current_user, plan_id)
    return serialize_plan(plan)


@router.patch("/{plan_id}", response_model=TravelPlanRead)
async def update_plan(
    plan_id: int,
    payload: TravelPlanUpdate,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = PlanningService(session)
    updated = await service.update_plan(current_user, plan_id, payload.model_dump(exclude_unset=True))
    return serialize_plan(updated)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_db_session),
):
    service = PlanningService(session)
    await service.delete_plan(current_user, plan_id)
