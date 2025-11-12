from fastapi import APIRouter

from .endpoints import auth, plans, expenses, speech, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(expenses.router, prefix="/plans/{plan_id}/expenses", tags=["expenses"])
api_router.include_router(speech.router, prefix="/speech", tags=["speech"])
