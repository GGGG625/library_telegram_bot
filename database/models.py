from sqlalchemy import String, INT, BigInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    ...

class Base_book(DeclarativeBase):
    id_book:Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class Users(Base):
    __tablename__ = 'users'
    id:Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_user:Mapped[int]
    name_user:Mapped[str]


class Admins(Base):
    __tablename__ = "admins"
    id:Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    id_admin:Mapped[int] = mapped_column(BigInteger, nullable=False)
    name_admin:Mapped[str] = mapped_column(String(150), nullable=False)

class Section_book(Base):
    __tablename__ = "section_book"
    id:Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_section:Mapped[str] = mapped_column(String(150), nullable=False)

class Book(Base_book):
    __tablename__="book"

    name_book:Mapped[str] = mapped_column(String(150), nullable=False)
    number_volume:Mapped[int] = mapped_column(INT, nullable=False)
    id_section:Mapped[int] = mapped_column(INT, nullable=False)
    year_publication:Mapped[int] = mapped_column(INT, nullable=False)
    presence:Mapped[bool] = mapped_column(Boolean, nullable=True)
    presence_id_user:Mapped[int] = mapped_column(BigInteger, nullable=False)
    presence_name_user:Mapped[str] = mapped_column(String(150), nullable=False)
    name_author:Mapped[str] = mapped_column(String(200), nullable=False)
    number_instance:Mapped[int] = mapped_column(INT, nullable=False)
