from string import punctuation
from aiogram import types, Router, F
from aiogram.filters import Command, or_f, StateFilter
from filters.user_types import IsAdmin
from keyboards.reply import get_keyboard
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from message.check import check_lot
from handlers.user_private import Cancel_KeyBoard, OTHER_KeyBoard, Yes_No_KeyBoard
from aiogram import Bot
from database.models import Admins, Users, Section_book, Book
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

admin_private_router = Router()
admin_private_router.message.filter(IsAdmin())

ADMIN_KeyBoard = get_keyboard(
    "Добавление/удаление книги",
    "Cписок книг у пользователя",
    "Управление админами/пользователями",
    placeholder = "Что вас интересует?",
    sizes=(2,1)
)

Action_KeyBoard = get_keyboard(
    "Добавление книги",
    "Удаление книги",
    "Отмена",
    sizes=(2,1)
)

Control_user_admin_KeyBoard = get_keyboard(
    "Список всех пользователей",
    "Список всех админов",
    "Добавление админа",#проверки есть, clear есть, бд есть
    "Удаление админа",
    "Удаление пользователя",
    "Отмена",
    sizes=(2,3,1)
)

class back (StatesGroup):
    back = State()

@admin_private_router.message(StateFilter('*'), Command('admin'))
async def start_handler(message: types.Message, state:FSMContext):
    await message.answer("Разрешено в доступе",reply_markup=ADMIN_KeyBoard)
    await state.clear()

@admin_private_router.message(StateFilter(None), F.text.casefold() == 'добавление/удаление книги') 
async def photo_handler(message:types.Message, state: FSMContext):
    await message.answer('Выберите что-то из этого',reply_markup=Action_KeyBoard)
    await state.set_state(back.back)

@admin_private_router.message(StateFilter(None), F.text.casefold() == "cписок книг у пользователя")
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Введите id пользователя', reply_markup=Cancel_KeyBoard)
    await state.set_state(user_books.id_user)

@admin_private_router.message(StateFilter(None), F.text.casefold() == 'управление админами/пользователями')
async def photo_handler(message:types.Message, state: FSMContext):
    await message.answer('Выберите что-то из этого',reply_markup=Control_user_admin_KeyBoard)
    await state.set_state(back.back)

@admin_private_router.message(back.back, F.text.casefold() == 'отмена')    
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class add_book(StatesGroup):
    book_name = State()
    book_number_volume = State()
    number_section = State()
    book_year_publication = State()
    book_author = State()
    add_confirm = State()
    number_instance = State()
    presence_id_user = State()
    presence_name_user = State()
    presence = State()

    text = {
    'add_book:book_name':'Введите название книги заново',
    'add_book:book_number_volume':'Введите номер тома (или 0) заново',
    'add_book:book_year_publication':'Введите год публикации заново',
    'add_book:book_author':'Введите автора/-ов заново',
    'add_book:add_confirm':'Подтверждаете?',
    }


@admin_private_router.message(add_book.book_name, F.text.casefold() == 'отмена')    
@admin_private_router.message(add_book.book_number_volume, F.text.casefold() == 'отмена')   
@admin_private_router.message(add_book.book_year_publication, F.text.casefold() == 'отмена')   
@admin_private_router.message(add_book.book_author, F.text.casefold() == 'отмена')     
@admin_private_router.message(add_book.add_confirm, F.text.casefold() == 'отмена')   
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)


@admin_private_router.message(back.back, F.text.casefold() == 'добавление книги')
async def photo_handler(message:types.Message, state: FSMContext):
    await message.answer('Введите название книги',reply_markup=Cancel_KeyBoard)
    await state.set_state(add_book.book_name)


@admin_private_router.message(add_book.book_name, F.text.casefold() == 'назад')     
@admin_private_router.message(add_book.book_number_volume, F.text.casefold() == 'назад')     
@admin_private_router.message(add_book.book_year_publication, F.text.casefold() == 'назад')  
@admin_private_router.message(add_book.book_author, F.text.casefold() == 'назад')  
@admin_private_router.message(add_book.add_confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == 'нет'))
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == add_book.book_name:
        await state.clear()
        await message.answer("Действия отменены", reply_markup=Action_KeyBoard)
    if current_state == add_book.add_confirm:
        await state.set_state(add_book.book_author)
        await message.answer("Введите автора/-ов заново", reply_markup=OTHER_KeyBoard)
    previous = None
    for step in  add_book.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f'{add_book.text[previous.state]}', reply_markup=OTHER_KeyBoard)
            return
        previous = step


@admin_private_router.message(add_book.book_name, F.text)
async def qr_photo(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "letters and numbers", 2, 200)
    if temp == True:
        await state.update_data(book_name=message.text.lower())
        await message.answer('Введите номер тома (или 0)', reply_markup=OTHER_KeyBoard)
        await state.set_state(add_book.book_number_volume)
    else: await message.answer(temp)


@admin_private_router.message(add_book.book_name)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=Cancel_KeyBoard)


@admin_private_router.message(add_book.book_number_volume, F.text)
async def qr_first(message: types.Message, state: FSMContext, session:AsyncSession):
    temp = check_lot(str(message.text), "numbers", 1, 2)
    if temp == True:
        await state.update_data(book_number_volume=message.text.lower())
        try:
            name_section = select(Section_book.id, Section_book.name_section)
            result_name_section = await session.execute(name_section)
            result_name_section = result_name_section.all()
            temp=""
            for i in result_name_section:
                temp+=f"{i.name_section} -> {i.id} \n"
            await message.answer(f"{str(temp)}\n\nВведите номер раздела", reply_markup=OTHER_KeyBoard)
            await state.set_state(add_book.number_section)
        except:
            await message.answer("Ошибка при подключении к бд", reply_markup=OTHER_KeyBoard)
    else: await message.answer(temp, reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.book_number_volume)
async def qr_first(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.number_section, F.text)
async def qr_first(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 1, 1)
    if temp == True:
        await state.update_data(number_section=message.text.lower())
        await message.answer('Введите номер экземпляра', reply_markup=OTHER_KeyBoard)
        await state.set_state(add_book.number_instance)
    else: await message.answer(temp, reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.number_section)
async def qr_first(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.number_instance, F.text)
async def qr_first(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 1, 2)
    if temp == True:
        await state.update_data(number_instance=message.text.lower())
        await message.answer('Введите год издания', reply_markup=OTHER_KeyBoard)
        await state.set_state(add_book.book_year_publication)
    else: await message.answer(temp, reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.number_section)
async def qr_first(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.book_year_publication, F.text)
async def qr_patronymic(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 3, 4)
    if temp == True:
        await state.update_data(book_year_publication=message.text.lower())
        await message.answer('Введите автора/-ов (через запятую)', reply_markup=OTHER_KeyBoard)
        await state.set_state(add_book.book_author)
    else: await message.answer(temp, reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.book_year_publication)
async def qr_patronymic(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.book_author, F.text)
async def qr_patronymic(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "letters", 1, 200)
    if temp == True:
        await state.update_data(book_author=message.text.lower())
        data = await state.get_data()
        book_name = data.get('book_name')
        book_number_volume = data.get('book_number_volume')
        number_section = data.get('number_section')
        number_instance = data.get('number_instance')
        book_year_publication = data.get('book_year_publication')
        book_author = data.get('book_author')
        await message.answer(f'Название -> {book_name}\nНомер тома -> {book_number_volume}\nНомер раздела -> {number_section}\nГод публикации -> {book_year_publication}\nАвтор/-ы -> {book_author}\nНомер экземпляра -> {number_instance}\n\nПодтверждаете?', reply_markup=Yes_No_KeyBoard)
        await state.set_state(add_book.add_confirm)
    else: await message.answer(temp, reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.book_author)
async def qr_patronymic(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(add_book.add_confirm, F.text.casefold()=="да")
async def qr_patronymic(message: types.Message, state: FSMContext, session:AsyncSession):
    data = await state.get_data()
    try:
        obj = Book(
            name_book=data['book_name'],
            number_volume=int(data['book_number_volume']),
            id_section=int(data['number_section']),
            year_publication=int(data['book_year_publication']),
            presence = False,
            presence_id_user = 0,
            presence_name_user = 0,
            name_author=data['book_author'],
            number_instance = int(data['number_instance']),
        )
        session.add(obj)
        await session.commit()
        await message.answer("Книга добавлена", reply_markup=ADMIN_KeyBoard)
        await state.clear()
    except Exception as e:
        await message.answer("Ошибка, данные не занесены в бд", reply_markup=ADMIN_KeyBoard)
        await state.clear()
        

@admin_private_router.message(add_book.add_confirm)
async def qr_patronymic(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class delete_book(StatesGroup):
    id_book = State()
    confirm = State()


@admin_private_router.message(delete_book.id_book, F.text.casefold() == 'отмена')    
@admin_private_router.message(delete_book.confirm, F.text.casefold() == 'отмена')   
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)


@admin_private_router.message(delete_book.id_book, F.text.casefold() == 'назад')   
@admin_private_router.message(delete_book.confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == "нет"))   
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    print(current_state)
    if current_state == delete_book.id_book:
        await state.clear()
        await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)
    if current_state == delete_book.confirm:
        await state.set_state(delete_book.id_book)
        await message.answer("Введите id книги", reply_markup=Cancel_KeyBoard)


@admin_private_router.message(back.back, F.text.casefold() == "удаление книги")
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Введите id книги', reply_markup=Cancel_KeyBoard)
    await state.set_state(delete_book.id_book)


@admin_private_router.message(delete_book.id_book, F.text)
async def search_book_name(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 1, 3)
    if temp == True:
        await state.update_data(id_book=message.text.lower())
        data = await state.get_data()
        #вывод этой книги (название и авторы)
        id_this_book = str(data.get('id_book'))
        await message.answer(f'id книги {id_this_book}. Подтвердить?', reply_markup=Yes_No_KeyBoard)
        await state.set_state(delete_book.confirm)
    else: await message.answer(temp)


@admin_private_router.message(delete_book.id_book)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=Cancel_KeyBoard)


@admin_private_router.message(delete_book.confirm, F.text.casefold() == "да")
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        data = await state.get_data()
        id_book = data.get("id_book")
        query = delete(Book).where(Book.id_book==int(id_book))
        await session.execute(query)
        await session.commit()
        await message.answer("Книга удалена", reply_markup=ADMIN_KeyBoard)
        await state.clear()
    except:
        await message.answer("Ошибка в бд, такого id нет", reply_markup=ADMIN_KeyBoard)
        await state.clear()


@admin_private_router.message(delete_book.confirm)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class user_books(StatesGroup):
    id_user = State()


@admin_private_router.message(user_books.id_user, F.text.casefold() == 'отмена')    
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)


@admin_private_router.message(user_books.id_user, F.text)
async def search_book_name(message: types.Message, state: FSMContext , session:AsyncSession):
    temp = check_lot(str(message.text), "numbers", 7, 10)
    if temp == True:
        await state.update_data(id_user=message.text.lower())
        data = await state.get_data()
        id_user = str(data.get('id_user'))
        try:
            books_user = select(Book.name_book, Book.number_volume, Book.id_section, Book.year_publication, Book.name_author, Book.number_instance).where(Book.presence_id_user == int(id_user))
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
            await message.answer(f"{temp}", reply_markup=ADMIN_KeyBoard)
        except:
            await message.answer("Ошибка, книг в бд нет", reply_markup=ADMIN_KeyBoard)

    else: await message.answer(temp)


@admin_private_router.message(user_books.id_user)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=Cancel_KeyBoard)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class new_admin (StatesGroup):
    new_id = State()
    name = State()
    confirm = State()

@admin_private_router.message(new_admin.new_id, F.text.casefold() == 'отмена')    
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)


@admin_private_router.message(new_admin.new_id, F.text.casefold() == 'назад')   
@admin_private_router.message(new_admin.confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == "нет"))   
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == new_admin.new_id:
        await state.clear()
        await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)
    if current_state == new_admin.confirm:
        await state.set_state(new_admin.new_id)
        await message.answer("Введите id пользователя", reply_markup=Cancel_KeyBoard)


@admin_private_router.message(back.back, F.text.casefold() == 'добавление админа')
async def id(message: types.Message, state: FSMContext):
    await message.answer('Введите id пользователя', reply_markup=Cancel_KeyBoard)
    await state.set_state(new_admin.new_id)


@admin_private_router.message(new_admin.new_id, F.text)
async def name_book(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 7, 10)
    if temp == True:
        await state.update_data(new_id=message.text.lower())
        await message.answer('Введите инициалы админа', reply_markup=Yes_No_KeyBoard)
        await state.set_state(new_admin.name)
    else: await message.answer(temp)


@admin_private_router.message(new_admin.name, F.text)
async def name_book(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "letters", 1, 100)
    if temp == True:
        await state.update_data(name=message.text.lower())
        data = await state.get_data()
        id = str(data.get('new_id'))
        name = str(data.get('name'))
        await message.answer(f'name -> {name}\n`id` -> {id}\nПодтвердить?', reply_markup=Yes_No_KeyBoard, parse_mode='Markdown')
        await state.set_state(new_admin.confirm)
    else: await message.answer(temp)


@admin_private_router.message(new_admin.name)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(new_admin.confirm, F.text.casefold() == "да")
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    data = await state.get_data()
    try:
        obj = Admins(
            id_admin=data['new_id'],
            name_admin=str(data['name']),
        )
        session.add(obj)
        await session.commit()
        await message.answer("Админ добавлен", reply_markup=ADMIN_KeyBoard)
        await state.clear()
    except Exception as e:
        await message.answer("Ошибка, данные не занесены в бд", reply_markup=ADMIN_KeyBoard)
        await state.clear()


@admin_private_router.message(new_admin.confirm)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@admin_private_router.message(back.back, F.text.casefold() == "список всех пользователей")
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        id_user = select(Users.id_user, Users.name_user)
        result_id_user = await session.execute(id_user)
        result_id_user = result_id_user.all()
        temp=""
        for i in result_id_user:
            temp+=f"{i.name_user} -> `{i.id_user}`\n"
        await message.answer(f"{str(temp)}", reply_markup=ADMIN_KeyBoard, parse_mode='Markdown')
        await state.clear()
    except Exception as e:
        await message.answer("Ошибка в бд", reply_markup=ADMIN_KeyBoard)
        await state.clear()


#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@admin_private_router.message(back.back, F.text.casefold() == "список всех админов")
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        id_admin = select(Admins.id_admin, Admins.name_admin)
        result_id_admin = await session.execute(id_admin)
        result_id_admin = result_id_admin.all()
        temp=""
        for i in result_id_admin:
            temp+=f"`{i.name_admin}` -> {i.id_admin} \n"
        await message.answer(f"{str(temp)}", reply_markup=ADMIN_KeyBoard, parse_mode='Markdown')
        await state.clear()
    except Exception as e:
        await message.answer("Ошибка в бд", reply_markup=ADMIN_KeyBoard)
        await state.clear()



#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class delete_admin (StatesGroup):
    id = State()
    confirm = State()

@admin_private_router.message(delete_admin.id, F.text.casefold() == 'отмена')    
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)


@admin_private_router.message(delete_admin.id, F.text.casefold() == 'назад')   
@admin_private_router.message(delete_admin.confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == "нет"))   
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == delete_admin.id:
        await state.clear()
        await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)
    if current_state == delete_admin.confirm:
        await state.set_state(delete_admin.id)
        await message.answer("Введите id админа", reply_markup=Cancel_KeyBoard)


@admin_private_router.message(back.back, F.text.lower() == 'удаление админа')
async def id(message: types.Message, state:FSMContext):
    await message.answer('Введите id пользователя', reply_markup=Cancel_KeyBoard)
    await state.set_state(delete_admin.id)


@admin_private_router.message(delete_admin.id, F.text)
async def name_book(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 1, 12)
    if temp == True:
        await state.update_data(id=message.text.lower())
        data = await state.get_data()
        id = str(data.get('id'))
        await message.answer(f'Удалить админа {id}\nПодтвердить?', reply_markup=Yes_No_KeyBoard, parse_mode='Markdown')
        await state.set_state(delete_admin.confirm)
    else: await message.answer(temp)


@admin_private_router.message(delete_admin.id)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(delete_admin.confirm, F.text.casefold() == "да")
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        data = await state.get_data()
        admin_id = data.get("id")
        query = delete(Admins).where(Admins.id_admin==admin_id)
        await session.execute(query)
        await session.commit()
        await message.answer("Админ удален", reply_markup=ADMIN_KeyBoard)
        await state.clear()
    except:
        await message.answer("Ошибка в бд, такого id нет", reply_markup=ADMIN_KeyBoard)
        await state.clear()


@admin_private_router.message(delete_admin.confirm)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


class delete_user (StatesGroup):
    id = State()
    confirm = State()

@admin_private_router.message(delete_user.id, F.text.casefold() == 'отмена')    
async def back_cmd(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)


@admin_private_router.message(delete_user.id, F.text.casefold() == 'назад')   
@admin_private_router.message(delete_user.confirm, or_f(F.text.casefold() == 'назад', F.text.casefold() == "нет"))   
async def cancel_cmd(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state == delete_user.id:
        await state.clear()
        await message.answer("Действия отменены", reply_markup=ADMIN_KeyBoard)
    if current_state == delete_user.confirm:
        await state.set_state(delete_user.id)
        await message.answer("Введите id пользователя", reply_markup=Cancel_KeyBoard)


@admin_private_router.message(back.back, F.text.lower() == 'удаление пользователя')
async def id(message: types.Message, state:FSMContext):
    await message.answer('Введите id пользователя', reply_markup=Cancel_KeyBoard)
    await state.set_state(delete_user.id)


@admin_private_router.message(delete_user.id, F.text)
async def name_book(message: types.Message, state: FSMContext):
    temp = check_lot(str(message.text), "numbers", 1, 12)
    if temp == True:
        await state.update_data(id=message.text.lower())
        data = await state.get_data()
        id = str(data.get('id'))
        #вывод id и name из бд
        await message.answer(f'Удалить пользователя [{None}](tg://user?id={id})\nПодтвердить?', reply_markup=Yes_No_KeyBoard)
        await state.set_state(delete_user.confirm)
    else: await message.answer(temp)


@admin_private_router.message(delete_user.id)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


@admin_private_router.message(delete_user.confirm, F.text.casefold() == "да")
async def search_book_name(message: types.Message, state: FSMContext, session:AsyncSession):
    try:
        data = await state.get_data()
        user_id = data.get("id")
        query = delete(Users).where(Users.id_user==int(user_id))
        await session.execute(query)
        await session.commit()
        await message.answer("Пользователь удален", reply_markup=ADMIN_KeyBoard)
        await state.clear()
    except:
        await message.answer("Ошибка в бд, такого id нет", reply_markup=ADMIN_KeyBoard)
        await state.clear()


@admin_private_router.message(delete_user.confirm)
async def search_book_name(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=OTHER_KeyBoard)


#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


@admin_private_router.message(back.back)
async def qr_photo(message: types.Message, state: FSMContext):
    await message.answer('Ошибка, попробуйте снова', reply_markup=ADMIN_KeyBoard)