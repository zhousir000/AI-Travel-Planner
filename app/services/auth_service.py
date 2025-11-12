from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import security
from ..repositories.user_repository import UserRepository
from ..schemas.auth import UserRegister


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = UserRepository(session)

    async def register(self, payload: UserRegister):
        existing = await self.repo.get_by_email(payload.email)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
        hashed_password = security.get_password_hash(payload.password)
        user = await self.repo.create(
            email=payload.email,
            hashed_password=hashed_password,
            full_name=payload.full_name,
        )
        await self.session.commit()
        return user

    async def authenticate(self, email: str, password: str):
        user = await self.repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        if not security.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        return user
