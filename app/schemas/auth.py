from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int


class TokenPayload(BaseModel):
    sub: str | None = None
    exp: int | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str | None = None


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
