from typing import Any
from aiogram.filters import Filter
from aiogram import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Users, Admins

class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, session:AsyncSession) -> bool:
        query = select(Admins.id_admin)
        result = await session.execute(query)
        result = str(result.all())
        return str(message.from_user.id) in result


class IsUser(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: types.Message, session:AsyncSession) -> bool:
        query = select(Users.id_user)
        result = await session.execute(query)
        result = str(result.all())
        return str(message.from_user.id) in result
    