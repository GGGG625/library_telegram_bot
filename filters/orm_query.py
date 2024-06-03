from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from database.models import Book


async def update_database(session:AsyncSession,name_book, number_volume,id_section,year_publication, name_author,number_instance, user_id, user_name, id_book, presence:bool):
    query = update(Book).where(Book.id_book == id_book).values(
                name_book = name_book,
                number_volume = number_volume,
                id_section = id_section,
                year_publication = year_publication,
                name_author = name_author,
                number_instance = number_instance,
                presence = presence,
                presence_id_user = user_id,
                presence_name_user = user_name,
    )
    await session.execute(query)
    await session.commit()
