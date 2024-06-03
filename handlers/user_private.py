from aiogram import types, Router, F
from aiogram.filters import Command, CommandStart, or_f, StateFilter
from keyboards.reply import get_keyboard
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from message.check import check_lot
from filters.user_types import IsUser
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql.operators import ilike_op
from database.models import Users, Book, Section_book
import os
from pyzbar.pyzbar import decode
from PIL import Image
import os
from filters.orm_query import update_database
from PIL import Image

user_private_router = Router()
user_private_router.message.filter(IsUser())


Start_KeyBoard = get_keyboard(
    "Список всех книг",
    "Взять/вернуть книгу",
    "Добавление пользователя",
    "Написать пользователю",
    placeholder = "Что вас интересует?",
    sizes=(3,3)
)


Cancel_KeyBoard = get_keyboard(
    "Отмена",
    sizes=(1,1)
)


OTHER_KeyBoard = get_keyboard(
    "Отмена",
    "Назад",
    sizes=(2,1)
)


List_books_KeyBoard = get_keyboard(
    "Поиск книги по названию",
    "Поиск книги по автору",
    "Фильтр книг по разделам",
    "Отслеживание своих книг",
    "Отмена",
    sizes=(3,2)
)


Take_return_KeyBoard = get_keyboard(
    "Взять книгу",
    "Вернуть книгу",
    "Отмена",
    sizes=(2,2)
)


Yes_No_KeyBoard = get_keyboard(
    "Да",
    "Нет",
    "Отмена",
    sizes=(2,2)
)


@user_private_router.message(StateFilter('*'), CommandStart())
async def start_cmd(message: types.Message, state:FSMContext):
    await message.answer("Привет, я виртуальный помощник", reply_markup=Start_KeyBoard)
    await state.clear()

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class books(StatesGroup):
    list_books = State()
    name = State()
    author = State()
    books_section = State()
    books_filters = State()
    my_books = State()

@user_private_router.message(StateFilter(None), or_f(Command('list_books'), F.text.casefold() == "список всех книг"))
async def search_book_name(message: types.Message, state: FSMContext):
    await state.set_state(books.list_books)
    await message.answer("Выберите что-то из этого",reply_markup=List_books_KeyBoard)


@user_private_router.message(books.list_books, F.text.casefold() == 'назад')
@user_private_router.message(books.name, F.text.casefold() == 'назад')
@user_private_router.message(books.author, F.text.casefold() == 'назад')   
@user_private_router.message(books.books_section, F.text.casefold() == 'назад')     
@user_private_router.message(books.my_books, F.text.casefold() == 'назад')     
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    await state.set_state(books.list_books)
    await message.answer("Действия отменены", reply_markup=List_books_KeyBoard)


@user_private_router.message(books.list_books, F.text.casefold() == 'отмена')    
@user_private_router.message(books.name, F.text.casefold() == 'отмена')  
@user_private_router.message(books.author, F.text.casefold() == 'отмена')  
@user_private_router.message(books.books_section, F.text.casefold() == 'отмена')  
@user_private_router.message(books.books_filters, F.text.casefold() == 'отмена')  
@user_private_router.message(books.my_books, F.text.casefold() == 'отмена')  
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Действия отменены", reply_markup=Start_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@user_private_router.message(books.list_books, F.text.casefold() == "поиск книги по названию")
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Введите название книги или часть названия', reply_markup=OTHER_KeyBoard)
    await state.set_state(books.name)


@user_private_router.message(books.name, F.text)
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    temp = check_lot(str(message.text), "letters and numbers", 1, 200)
    if temp == True:
        await state.update_data(name=message.text.lower())
        data = await state.get_data()
        name_book = data.get('name')
        try:
            books = select(Book.name_book, Book.name_author, Book.presence_name_user, Book.presence_id_user).group_by(Book.name_book and Book.number_instance).filter(ilike_op(Book.name_book,f'%{name_book}%'))
            result_books = await session.execute(books)
            result_books = result_books.all()
            temp=""
            temp1=""
            user_book = select(Book.presence_id_user, Book.presence_name_user).where(Book.presence==1).filter(ilike_op(Book.name_book,f'%{name_book}%'))
            result_user = await session.execute(user_book)
            result_user = result_user.all()
            for i in result_books:
                name_book = i.name_book
                user_book = select(Book.presence_id_user, Book.presence_name_user).where(Book.name_book == name_book).where(Book.presence==1)
                result_user = await session.execute(user_book)
                result_user = result_user.all()
                temp+=f"Название -> {i.name_book}\nАвтор/-ы -> {i.name_author} \nЭкземпляр -> {i.number_instance}\nИмя -> {i.presence_name_user}  Id -> `{i.presence_id_user}`\n\n"
            await message.answer(f"{str(temp)}", reply_markup=Start_KeyBoard, parse_mode='Markdown')
            await state.clear()
        except Exception as e:
            await message.answer("Ошибка в бд, совпадений не найдено", reply_markup=Start_KeyBoard)
            await state.clear()
    else: await message.answer(temp)

@user_private_router.message(books.name)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@user_private_router.message(books.list_books, F.text.casefold() == "поиск книги по автору")
async def search_book_author(message: types.Message, state: FSMContext):
    await message.answer('Введите автора (Фамилия Имя Отчество)', reply_markup=OTHER_KeyBoard)
    await state.set_state(books.author)


@user_private_router.message(books.author, F.text)
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    temp = check_lot(str(message.text), "letters and numbers", 1, 200)
    if temp == True:
        await state.update_data(author=message.text.lower())
        data = await state.get_data()
        author = data.get('author')
        try:
            authors = select(Book.name_book, Book.name_author, Book.presence_id_user, Book.presence_name_user, Book.number_instance).group_by(Book.name_book).filter(ilike_op(Book.name_author,f'%{author}%'))
            result_author = await session.execute(authors)
            result_author = result_author.all()
            temp=""
            for i in result_author:
                name_book = i.name_book
                user_book = select(Book.presence_id_user, Book.presence_name_user).where(Book.presence==1 and Book.name_book == name_book)
                result_user = await session.execute(user_book)
                result_user = result_user.all()
                temp+=f"Название -> {i.name_book}\nАвтор/-ы -> {i.name_author} \nЭкземпляр -> {i.number_instance}\nИмя -> {i.presence_name_user}  Id -> `{i.presence_id_user}`\n\n"
            await message.answer(f"{str(temp)}", reply_markup=Start_KeyBoard, parse_mode='Markdown')
            await state.clear()
        except Exception as e:
            await message.answer("Ошибка в бд, совпадений не найдено", reply_markup=Start_KeyBoard)
            await state.clear()
    else: await message.answer(temp)


@user_private_router.message(books.author)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@user_private_router.message(books.list_books, F.text.casefold() == "фильтр книг по разделам")
async def search_book_author(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        name_section = select(Section_book.id, Section_book.name_section)
        result_name_section = await session.execute(name_section)
        result_name_section = result_name_section.all()
        temp=""
        for i in result_name_section:
            temp+=f"{i.name_section} -> {i.id} \n"
        await message.answer(f"{str(temp)}\n\nВведите номер раздела", reply_markup=OTHER_KeyBoard)
        await state.set_state(books.books_section)
    except:
        await message.answer("Ошибка при подключении к бд", reply_markup=OTHER_KeyBoard)
    


@user_private_router.message(books.books_section, F.text)
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    temp = check_lot(str(message.text), "numbers", 1, 1)
    if temp == True:
        await state.update_data(books_section=message.text.lower())
        data = await state.get_data()
        section = data.get('books_section')
        try:
            books_section = select(Book.name_book, Book.name_author).where(Book.id_section == int(section)).group_by(Book.name_book)
            result_books = await session.execute(books_section)
            result_books = result_books.all()
            temp=""
            for i in result_books:
                temp+=f"название -> {i.name_book}\n автор/-ы -> {i.name_author} \n"
            await message.answer(f"{str(temp)}", reply_markup=Start_KeyBoard, parse_mode='Markdown')
            await state.clear()
        except Exception as e:
            await message.answer("Ошибка в бд, совпадений не найдено", reply_markup=Start_KeyBoard)
            await state.clear()
    else: await message.answer(temp)


@user_private_router.message(books.books_section)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@user_private_router.message(books.list_books, F.text.casefold() == "отслеживание своих книг")
async def search_book_author(message: types.Message, state: FSMContext, session:AsyncSession):
    await state.set_state(books.my_books)
    user_id = message.from_user.id
    try:
        books_user = select(Book.name_book, Book.number_volume, Book.id_section, Book.year_publication, Book.name_author, Book.number_instance).where(Book.presence_id_user == int(user_id))
        result_books_user = await session.execute(books_user)
        result_books_user = result_books_user.all()
        temp=""
        temp_section =""
        for i in result_books_user:
                    try:
                        id_section = int(i.id_section)
                        name_section = select(Section_book.name_section).where(Section_book.id == id_section)
                        result_name_section = await session.execute(name_section)
                        result_name_section = result_name_section.all()
                        for j in result_name_section:
                            temp_section = j.name_section
                    except: 
                        await message.answer("Ошибка при подключении к бд", reply_markup=OTHER_KeyBoard)
                    temp+=f"Название -> {i.name_book}\nНомер тома -> {i.number_volume}\nРаздел -> {temp_section}\nГод издания -> {i.year_publication}\nАвтор/-ы -> {i.name_author}\nНомер экземпляра -> {i.number_instance}\n\n"
    except:
        await message.answer("Ошибка при подключении к бд", reply_markup=OTHER_KeyBoard)
    await state.clear()
    try:
        await message.answer(f"{temp}", reply_markup=Start_KeyBoard)
    except:
        await message.answer("Ошибка, книг в бд нет", reply_markup=Start_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class qr_scan(StatesGroup):
    qr_scan = State()
    take_book = State()
    return_book = State()
    take_confirm = State()
    return_confirm = State()


@user_private_router.message(qr_scan.qr_scan, F.text.casefold() == 'отмена')    
@user_private_router.message(qr_scan.take_book, F.text.casefold() == 'отмена')  
@user_private_router.message(qr_scan.return_book, F.text.casefold() == 'отмена')  
@user_private_router.message(qr_scan.take_confirm, F.text.casefold() == 'отмена')  
@user_private_router.message(qr_scan.return_confirm, F.text.casefold() == 'отмена')  
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Действия отменены", reply_markup=Start_KeyBoard)


@user_private_router.message(qr_scan.take_book, F.text.casefold() == 'назад')
@user_private_router.message(qr_scan.take_confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == "нет"))   
@user_private_router.message(qr_scan.return_book, F.text.casefold() == 'назад')
@user_private_router.message(qr_scan.return_confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == "нет"))       
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if qr_scan.take_book == current_state:
        await state.set_state(qr_scan.qr_scan)
        await message.answer('Выберите что-то из этого',reply_markup=Take_return_KeyBoard)
    if qr_scan.take_confirm == current_state:
        await message.answer('Отправьте фото с qr-кодом', reply_markup=OTHER_KeyBoard)
        await state.set_state(qr_scan.take_book)
    if qr_scan.return_book == current_state:
        await state.set_state(qr_scan.qr_scan)
        await message.answer('Выберите что-то из этого',reply_markup=Take_return_KeyBoard)
    if qr_scan.return_confirm == current_state:
        await message.answer('Отправьте фото с qr-кодом', reply_markup=OTHER_KeyBoard)
        await state.set_state(qr_scan.take_book)
        

@user_private_router.message(StateFilter(None), F.text.casefold() == 'взять/вернуть книгу')
async def photo_handler(message:types.Message, state: FSMContext):
    await state.set_state(qr_scan.qr_scan)
    await message.answer('Выберите что-то из этого',reply_markup=Take_return_KeyBoard)


@user_private_router.message(qr_scan.qr_scan, F.text.casefold() == 'взять книгу')
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Отправьте фото с qr-кодом', reply_markup=OTHER_KeyBoard)
    await state.set_state(qr_scan.take_book)


@user_private_router.message(qr_scan.take_book, F.photo)
async def qr_photo(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        data = await state.get_data()
        await message.bot.download(file=message.photo[-1].file_id, destination='qrcode.png')
        result = decode(Image.open('qrcode.png'))
        os.remove("qrcode.png")
        id_book = result[0].data.decode('utf-8')
        id_book = int(id_book)
        await state.update_data(take_book=id_book)

        this_book = select(Book.name_book, Book.number_volume, Book.id_section, Book.year_publication, Book.name_author, Book.number_instance).where(Book.id_book == int(id_book))
        result_this_book = await session.execute(this_book)
        result_this_book = result_this_book.all()
        temp=""
        temp_section =""
        for i in result_this_book:
            try:
                id_section = int(i.id_section)
                name_section = select(Section_book.name_section).where(Section_book.id == id_section)
                result_name_section = await session.execute(name_section)
                result_name_section = result_name_section.all()
                for j in result_name_section:
                    temp_section = j.name_section
            except: 
                    await message.answer("Ошибка при подключении к бд", reply_markup=OTHER_KeyBoard)
                    return
            temp+=f"Название -> {i.name_book}\nНомер тома -> {i.number_volume}\nРаздел -> {temp_section}\nГод издания -> {i.year_publication}\nАвтор/-ы -> {i.name_author}\nНомер экземпляра -> {i.number_instance}\n\n"
        await message.answer(f"{temp}")
        await message.answer("Подтвердить?", reply_markup=Yes_No_KeyBoard)
        await state.set_state(qr_scan.take_confirm)
    except:
        await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)



@user_private_router.message(qr_scan.take_book)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@user_private_router.message(qr_scan.take_confirm, F.text.casefold() == 'да')
async def qr_photo(message: types.Message, state: FSMContext, session:AsyncSession):
    data = await state.get_data()
    id_book = data.get('take_book')
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    try:
        this_book = select(Book.name_book, Book.number_volume, Book.id_section, Book.year_publication, Book.name_author, Book.number_instance, Book.presence, Book.presence_id_user, Book.presence_name_user).where(Book.id_book == int(id_book))
        result_this_book = await session.execute(this_book)
        result_this_book = result_this_book.all()
        for i in result_this_book:
            name_book_i = str(i.name_book)
            number_volume_i = int(i.number_volume)
            id_section_i = int(i.id_section)
            year_publication_i = int(i.year_publication)
            name_author_i = str(i.name_author)
            number_instance_i = int(i.number_instance)

        await update_database(session=session, name_book=name_book_i, number_volume=number_volume_i, id_section=id_section_i,year_publication= year_publication_i,name_author= name_author_i, number_instance=number_instance_i, user_id=user_id, user_name=user_name, id_book=id_book, presence=True)
        await message.answer('Данные занесены', reply_markup=Start_KeyBoard)
        await state.clear()
    except:
        await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)
     

@user_private_router.message(qr_scan.take_confirm)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#=======================================================================================================


@user_private_router.message(qr_scan.qr_scan, F.text.casefold() == 'вернуть книгу')
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Отправьте фото с qr-кодом', reply_markup=OTHER_KeyBoard)
    await state.set_state(qr_scan.return_book)


@user_private_router.message(qr_scan.return_book, F.photo)
async def qr_photo(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        data = await state.get_data()
        await message.bot.download(file=message.photo[-1].file_id, destination='qrcode.png')
        result = decode(Image.open('qrcode.png'))
        os.remove("qrcode.png")
        id_book = result[0].data.decode('utf-8')
        id_book = int(id_book)
        await state.update_data(return_book=id_book)

        this_book = select(Book.name_book, Book.number_volume, Book.id_section, Book.year_publication, Book.name_author, Book.number_instance).where(Book.id_book == int(id_book))
        result_this_book = await session.execute(this_book)
        result_this_book = result_this_book.all()
        temp=""
        temp_section =""
        for i in result_this_book:
            try:
                id_section = int(i.id_section)
                name_section = select(Section_book.name_section).where(Section_book.id == id_section)
                result_name_section = await session.execute(name_section)
                result_name_section = result_name_section.all()
                for j in result_name_section:
                    temp_section = j.name_section
            except: 
                    await message.answer("Ошибка при подключении к бд", reply_markup=OTHER_KeyBoard)
                    return
            temp+=f"Название -> {i.name_book}\nНомер тома -> {i.number_volume}\nРаздел -> {temp_section}\nГод издания -> {i.year_publication}\nАвтор/-ы -> {i.name_author}\nНомер экземпляра -> {i.number_instance}\n\n"
        await message.answer(f"{temp}")
        await message.answer("Подтвердить?", reply_markup=Yes_No_KeyBoard)
        await state.set_state(qr_scan.return_confirm)
    except:
        await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@user_private_router.message(qr_scan.return_book)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@user_private_router.message(qr_scan.return_confirm, F.text.casefold() == 'да')
async def qr_photo(message: types.Message, state: FSMContext, session:AsyncSession):
    data = await state.get_data()
    id_book = data.get('return_book')
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    try:
        this_book = select(Book.name_book, Book.number_volume, Book.id_section, Book.year_publication, Book.name_author, Book.number_instance, Book.presence, Book.presence_id_user, Book.presence_name_user).where(Book.id_book == int(id_book))
        result_this_book = await session.execute(this_book)
        result_this_book = result_this_book.all()
        for i in result_this_book:
            name_book_i = str(i.name_book)
            number_volume_i = int(i.number_volume)
            id_section_i = int(i.id_section)
            year_publication_i = int(i.year_publication)
            name_author_i = str(i.name_author)
            number_instance_i = int(i.number_instance)

        await update_database(session=session, name_book=name_book_i, number_volume=number_volume_i, id_section=id_section_i,year_publication= year_publication_i,name_author= name_author_i, number_instance=number_instance_i, user_id=0, user_name="", id_book=id_book, presence=False)
        await message.answer('Данные удалены', reply_markup=Start_KeyBoard)
        await state.clear()
    except: 
        await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@user_private_router.message(qr_scan.return_confirm)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class add_user(StatesGroup):
    id_user = State()
    name = State()
    confirm = State()

    text = {
    'add_user:id_user':'Введите id пользователя заново',
    'add_user:name':'Введите фамилию заново',
    'add_user:confirm':'Подтверждаете?',
    }


@user_private_router.message(add_user.id_user, F.text.casefold() == 'отмена')    
@user_private_router.message(add_user.name, F.text.casefold() == 'отмена')  
@user_private_router.message(add_user.confirm, F.text.casefold() == 'отмена')  
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=Start_KeyBoard)


@user_private_router.message(StateFilter(None), F.text.casefold() == 'добавление пользователя'))
async def photo_handler(message:types.Message, state: FSMContext):
    await message.answer('Введите id пользователя',reply_markup=Cancel_KeyBoard)
    await state.set_state(add_user.id_user)


@user_private_router.message(add_user.name, F.text.casefold() == 'назад')   
@user_private_router.message(add_user.confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == 'нет'))
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == add_user.id_user:
        await state.clear()
        await message.answer("Действия отменены", reply_markup=Start_KeyBoard)
    previous = None
    for step in  add_user.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f'{add_user.text[previous.state]}', reply_markup=OTHER_KeyBoard)
            return
        previous = step


@user_private_router.message(add_user.id_user, F.text)
async def qr_photo(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 7, 10)
    if temp == True:
        await state.update_data(id_user=message.text.lower())
        await message.answer('Введите инициалы', reply_markup=OTHER_KeyBoard)
        await state.set_state(add_user.name)
    else: await message.answer(temp)


@user_private_router.message(add_user.id_user)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=Cancel_KeyBoard)



@user_private_router.message(add_user.name, F.text)
async def photo_handler(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "letters", 1, 100)
    if temp == True:
        await state.update_data(name=message.text.lower())
        data = await state.get_data()
        name = str(data.get('name'))
        id_user = str(data.get('id_user'))
        await message.answer(f'id -> {id_user}\n{name}\nПодтверждаете?', reply_markup=Yes_No_KeyBoard)
        await state.set_state(add_user.confirm)
    else: await message.answer(temp, reply_markup=OTHER_KeyBoard)


@user_private_router.message(add_user.name)
async def photo_handler(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@user_private_router.message(add_user.confirm, F.text.casefold() == 'да')
async def qr_patronymic(message: types.Message, state: FSMContext, session:AsyncSession):
    data = await state.get_data()
    try:
        obj = Users(
            id_user=data['id_user'],
            name_user=str(data['name']),
        )
        session.add(obj)
        await session.commit()
        await message.answer("Данные занесены", reply_markup=Start_KeyBoard)
        await state.clear()
    except Exception as e:
        await message.answer("Ошибка, данные не занесены в бд", reply_markup=Start_KeyBoard)
        await state.clear()

@user_private_router.message(add_user.confirm)
async def qr_patronymic(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++=


class message_user(StatesGroup):
    id_user = State()
    text = State()
    confirm = State()


@user_private_router.message(message_user.id_user, F.text.casefold() == 'отмена')    
@user_private_router.message(message_user.text, F.text.casefold() == 'отмена')  
@user_private_router.message(message_user.confirm, F.text.casefold() == 'отмена')  
@user_private_router.message(books.books_section, F.text.casefold() == 'отмена')  
@user_private_router.message(books.books_filters, F.text.casefold() == 'отмена')  
@user_private_router.message(books.my_books, F.text.casefold() == 'отмена')  
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("Действия отменены", reply_markup=Start_KeyBoard)


@user_private_router.message(message_user.text, F.text.casefold() == 'назад')   
@user_private_router.message(message_user.confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == "нет"))   
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    if message_user.confirm == await state.get_state():
        await message.answer('Введите текст сообщения', reply_markup=Cancel_KeyBoard)
        await state.set_state(message_user.text)


@user_private_router.message(StateFilter(None), F.text.casefold() == "написать пользователю")
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Введите id пользователя', reply_markup=Cancel_KeyBoard)
    await state.set_state(message_user.id_user)


@user_private_router.message(message_user.id_user, F.text)
async def search_book_name(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 7, 10)
    if temp == True:
        await state.update_data(id_user=message.text.lower())
        await message.answer('Введите текст сообщения', reply_markup=Cancel_KeyBoard)
        await state.set_state(message_user.text)
    else: await message.answer(temp)


@user_private_router.message(message_user.id_user)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@user_private_router.message(message_user.text, F.text)
async def search_book_name(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "letters and numbers", 5, 100)
    if temp == True:
        await state.update_data(text=message.text)
        await message.answer('Подтвердить?', reply_markup=Yes_No_KeyBoard)
        await state.set_state(message_user.confirm)
    else: await message.answer(temp)


@user_private_router.message(message_user.text)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@user_private_router.message(message_user.confirm, F.text.casefold() == "да")
async def search_book_name(message: types.Message, state: FSMContext, bot:Bot):
    if message.chat.type == 'private':
        try:
            data = await state.get_data()
            text = str(data.get('text'))
            id_user = data.get('id_user')
            await bot.send_message(chat_id=id_user, text=f"{text} \n\nСообщение от пользователя [{message.from_user.first_name} {message.from_user.last_name}](tg://user?id={message.from_user.id})", parse_mode='Markdown')
            await message.answer("Сообщение отправлено", reply_markup=Start_KeyBoard)
        except:
            await message.answer("Ошибка, сообщение не отправлено", reply_markup=Start_KeyBoard)
        await state.clear()


@user_private_router.message(message_user.confirm)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#===================================================================================================================


@user_private_router.message(books.list_books)
async def search_book_author(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=List_books_KeyBoard)


@user_private_router.message(qr_scan.qr_scan)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)
