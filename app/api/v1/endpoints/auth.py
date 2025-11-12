from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from ....api.deps import get_db_session
from ....core import security
from ....core.config import settings
from ....schemas.auth import Token, UserLogin, UserProfile, UserRegister
from ....services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegister, session=Depends(get_db_session)):
    service = AuthService(session)
    user = await service.register(payload)
    return UserProfile.from_orm(user)


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, session=Depends(get_db_session)):
    service = AuthService(session)
    user = await service.authenticate(payload.email, payload.password)
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    token = security.create_access_token(subject=user.email, expires_delta=expires_delta)
    expires_in = int(expires_delta.total_seconds())
    return Token(access_token=token, expires_in=expires_in)
