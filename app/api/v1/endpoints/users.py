from fastapi import APIRouter, Depends

from ....api.deps import get_current_user
from ....models import User
from ....schemas.auth import UserProfile

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return UserProfile.from_orm(current_user)
