from sqlalchemy import text

from ..models import *  # noqa: F401,F403
from .base import Base
from .session import engine


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if conn.dialect.name == "sqlite":
            await conn.execute(text("PRAGMA foreign_keys=ON"))
