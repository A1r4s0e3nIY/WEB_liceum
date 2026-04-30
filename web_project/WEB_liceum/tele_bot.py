import asyncio
import pymorphy3
import os
import pytz
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.types import CallbackQuery, FSInputFile, URLInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
from calendar import monthrange
from data import db_session
from data.users import User
from data.plans import Plan
from data.events import Event

os.makedirs("images_dir", exist_ok=True)

bot = Bot("8573629235:AAFkezNHEOOT8ZxsyysACPPmrGu65LwSOwY") 
dp = Dispatcher()
chat_id = None


class Plans(StatesGroup):
    plan_add = State()
    plan_del = State()

class Reg(StatesGroup):
    time_input = State()

class Profile(StatesGroup):
    photo = State()
    timexone = State()

class Kallend(StatesGroup):
    date_add = State()
    date_del = State()
    date_check = State()
    date_month = State()
    time_check = State()

morph = pymorphy3.MorphAnalyzer()
months_buttons = {"dec": ["Декабрь❄", 12], "jan": ["Январь❄", 1], "feb": ["Февраль❄", 2], "mar": ["Март🌸", 3], "apr": ["Апрель🌸", 4], "may": ["Май🌸", 5], 
                "jun": ["Июнь☀", 6],"jul": ["Июль☀", 7], "aug": ["Август☀", 8], "sep": ["Сентябрь🍁", 9], "oct": ["Октябрь🍁", 10], "nov": ["Ноябрь🍁", 11]}
main_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Профиль")], [KeyboardButton(text="Планы на день")], [KeyboardButton(text="Календарь")]], resize_keyboard=True)
change_photo = InlineKeyboardButton(text="Установить новую картинку в профиле", callback_data="change_photo")
change_timezone = InlineKeyboardButton(text="Сменить часовой пояс", callback_data="start_reg")
start_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Открыть меню", callback_data="main_menu")]])
start_menu_bt = InlineKeyboardButton(text="Открыть меню 📑 ", callback_data="main_menu")
plans_add = InlineKeyboardButton(text="Добавить план✅ ", callback_data="plan_add")
plans_del = InlineKeyboardButton(text="Удалить план❌ ", callback_data="plan_del")
plans_check = InlineKeyboardButton(text="Посмотреть план 👀 ", callback_data="plan_check")
dates_add = InlineKeyboardButton(text="Добавить дату✅ ", callback_data="date_add")
dates_del = InlineKeyboardButton(text="Удалить дату❌ ", callback_data="date_del")
all_checks = InlineKeyboardButton(text="Посмотреть все даты 👀", callback_data="date_checks")
dates_change = InlineKeyboardButton(text="Изменить месяц↩ ", callback_data="date_change")
start_reg = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Начать регистрацию📃", callback_data="start_reg")]])
geopos_select = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Ваше местоположение❓", callback_data="pos_select")]])
geoposition = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Калининград(МСК-1)", callback_data="city_Калининград(МСК-1)")], 
                                                    [InlineKeyboardButton(text="Москва(МСК+0)", callback_data="city_Москва(МСК+0)")], 
                                                    [InlineKeyboardButton(text="Самара(МСК+1)", callback_data="city_Самара(МСК+1)")], 
                                                    [InlineKeyboardButton(text="Екатеринбург(МСК+2)", callback_data="city_Екатеринбург(МСК+2)")], 
                                                    [InlineKeyboardButton(text="Омск(МСК+3)", callback_data="city_Омск(МСК+3)")], 
                                                    [InlineKeyboardButton(text="Новосибирск(МСК+4)", callback_data="city_Новосибирск(МСК+4)")],
                                                    [InlineKeyboardButton(text="Красноярск(МСК+4)", callback_data="city_Красноярск(МСК+4)")], 
                                                    [InlineKeyboardButton(text="Иркутск(МСК+5)", callback_data="city_Иркутск(МСК+5)")], 
                                                    [InlineKeyboardButton(text="Якутск(МСК+6)", callback_data="city_Якутск(МСК+6)")], 
                                                    [InlineKeyboardButton(text="Владивосток(МСК+7)", callback_data="city_Владивосток(МСК+7)")],
                                                    [InlineKeyboardButton(text="Магадан(МСК+8)", callback_data="city_Магадан(МСК+8)")], 
                                                    [InlineKeyboardButton(text="Анадырь(МСК+9)", callback_data="city_Анадырь(МСК+9)")]])
all_plans = InlineKeyboardMarkup(inline_keyboard=[[plans_add], [plans_del], [plans_check], [start_menu_bt]])
plans_add_solo = InlineKeyboardMarkup(inline_keyboard=[[plans_add], [start_menu_bt]])
all_dates = InlineKeyboardMarkup(inline_keyboard=[[dates_add], [dates_del], [all_checks], [dates_change], [start_menu_bt]])
dates_add_solo = InlineKeyboardMarkup(inline_keyboard=[[dates_add], [dates_change], [start_menu_bt]])
check_profile = InlineKeyboardMarkup(inline_keyboard=[[change_timezone], [change_photo]])
city_offsets = {"Калининград(МСК-1)":"Europe/Kaliningrad", "Москва(МСК+0)": "Europe/Moscow", "Самара(МСК+1)": "Europe/Samara",
    "Екатеринбург(МСК+2)": "Asia/Yekaterinburg", "Омск(МСК+3)": "Asia/Omsk", "Новосибирск(МСК+4)": "Asia/Novosibirsk",
    "Красноярск(МСК+4)": "Asia/Krasnoyarsk", "Иркутск(МСК+5)": "Asia/Irkutsk", "Якутск(МСК+6)": "Asia/Yakutsk",
    "Владивосток(МСК+7)": "Asia/Vladivostok", "Магадан(МСК+8)": "Asia/Magadan", "Анадырь(МСК+9)": "Asia/Anadyr"}

@dp.message(CommandStart())
async def start(message: Message):
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if not session.get(User, user_id):
        await message.answer(f"""Привет, {message.from_user.first_name}!\nВ этом боте собраны все полезные функции для твоей ежедневной рутины.\nВы не зарегистрированы в системе - начните регистрацию:""", reply_markup=start_reg)
    else:
        await message.answer(f"""Привет, {message.from_user.first_name}! 
                             В этом боте собраны все полезные функции для твоей ежедневной рутины""", reply_markup=start_menu)
    session.commit()
    session.close()

@dp.callback_query(F.data == "start_reg")
async def registration(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.time_input)
    await callback.answer()
    await callback.message.answer("Укажите ваш город.\nЕсли Вы живете не в городе, или города, в котором Вы живете, нет, выберите ближайший к вам город из списка.", reply_markup=geoposition)
    
@dp.callback_query(F.data.startswith("city_"))
async def city_selected(callback: CallbackQuery, state: FSMContext):
    db_session.global_init("db/my_base.db")
    user_id = callback.from_user.id
    city_name = callback.data.split("_")[1]

    timezone_offset = city_offsets[city_name]
    
    await callback.answer()
    
    session = db_session.create_session()
    user = session.query(User).filter(User.uid == user_id).first()
    if user:
        user.city = city_name
        user.timezone = timezone_offset
        session.commit()
        await callback.message.answer("Вы успешно сменили часовой пояс", reply_markup=main_menu)
    else:
        user = User(uid=callback.from_user.id, name=callback.from_user.first_name, timezone=timezone_offset, city=city_name)
        session.add(user)
        session.commit()
        await callback.message.answer("Добро пожаловать!", reply_markup=main_menu)

    session.close()

@dp.message(F.text == "Профиль")
async def profile(message: Message):
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()
    user_id = message.from_user.id
    user = session.query(User).filter(User.uid == user_id).first()
    if not user:
        await message.answer("❌ Вы не зарегистрированы! Нажмите /start")
        session.close()
        return
    
    city = user.city
    name = user.name
    avatar_path = os.path.join("images_dir", f"{user_id}.jpg")  # ✅ исправлено
    
    if os.path.exists(avatar_path):
        photo = FSInputFile(avatar_path)
        await message.answer_photo(
            photo=photo,
            caption=f"""📱 Ваш профиль:\n👤 Имя: {name or "Не указано"}\n🌍 Часовой пояс: {city}""",
            reply_markup=check_profile
        )
    else:
        await message.answer(
            f"""📱 Ваш профиль:\n👤 Имя: {name or "Не указано"}\n🌍 Часовой пояс: {city}\n\n📸 У вас нет фото профиля. Нажмите «Сменить картинку», чтобы добавить.""",
            reply_markup=check_profile
        )
    
    session.close()

@dp.callback_query(F.data == "change_photo")
async def change_photo_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Profile.photo)
    await callback.answer()
    await callback.message.answer("📸 Отправьте новое фото для вашего профиля")

@dp.message(Profile.photo, F.photo)
async def save_profile_photo(message: Message, state: FSMContext):
    user_id = message.from_user.id
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    avatar_path = os.path.join("images_dir", f"{user_id}.jpg")
    await bot.download_file(file.file_path, avatar_path)
    
    await message.answer("✅ Фото профиля успешно обновлено!")
    await state.clear()

@dp.callback_query(F.data == "main_menu")
async def menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Вы в меню") 
    await callback.message.answer("Добро пожаловать!", reply_markup=main_menu)

@dp.message(F.text == "Планы на день")
async def plans(message: Message, state: FSMContext):
    await state.clear()
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()
    plans_list = []
    user_id = message.from_user.id
    for plan in session.query(Plan).filter(Plan.user_id == user_id):
        plans_list.append(plan.text)
    await message.answer(f"Вы в меню планов", reply_markup=all_plans if len(plans_list) else plans_add_solo)

    session.commit()
    session.close()

@dp.callback_query(F.data == "plan_add")
async def plans_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Plans.plan_add)
    await callback.answer()
    await callback.message.answer("Введите ваш план")

async def inline_plans(user_id):
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()
    plans_for_sth  = InlineKeyboardBuilder()
    for plan in session.query(Plan).filter(Plan.user_id == user_id):
        plans_for_sth.add(InlineKeyboardButton(text=plan.text, callback_data=f"{plan.text}"))
    return plans_for_sth.adjust(3).as_markup()
    
@dp.callback_query(F.data == "plan_del")
async def plans_del(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await state.set_state(Plans.plan_del)
    await callback.answer()
    await callback.message.answer("Выберите план для удаления", reply_markup=await inline_plans(user_id))
    
@dp.message(Plans.plan_add)
async def plan_add(message: Message, state: FSMContext):
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()
    plan_text = message.text
    user_id = message.from_user.id
    plan = Plan(user_id=user_id, text=plan_text)
    session.add(plan)
    await message.answer(f"План успешно добавлен")
    await message.answer("Вы в меню планов", reply_markup=all_plans)
    await state.clear()
    session.commit()
    session.close()

@dp.callback_query(Plans.plan_del)
async def plan_del(callback_query: CallbackQuery, state: FSMContext): 
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()
    user_id = callback_query.from_user.id
    plan_text = callback_query.data
    plan = session.query(Plan).filter(Plan.user_id == user_id, Plan.text == plan_text).first()
    session.delete(plan)
    plans_list = []
    for plan in session.query(Plan).filter(Plan.user_id == user_id):
        plans_list.append(plan.text)
    await state.clear()
    await callback_query.answer()
    await callback_query.message.answer(f"План успешно удалён")
    await callback_query.message.answer(f"Вы в меню планов", reply_markup=all_plans if plans_list else plans_add_solo)
    session.commit()
    session.close()

@dp.callback_query(F.data == "plan_check")
async def plans_check(callback_query: CallbackQuery):
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()
    user_id = callback_query.from_user.id
    plans_list = []
    for plan in session.query(Plan).filter(Plan.user_id == user_id):
        plans_list.append(plan.text)
    await callback_query.answer()
    await callback_query.message.answer(f"Ваши планы на сегодня:\n{"\n".join(plans_list)}", reply_markup=all_plans)

    session.commit()
    session.close()
    
@dp.message(F.text == "Календарь")
async def kallen(message: Message, state: FSMContext):
    await message.answer("Выберите месяц >>>", reply_markup=await set_months())

async def set_months():
    months = InlineKeyboardBuilder()
    for month in months_buttons:
        months.add(InlineKeyboardButton(text=months_buttons[month][0], callback_data=f"{month}"))
    months.add(start_menu_bt)
    return months.adjust(3).as_markup()

@dp.callback_query(lambda call: call.data in months_buttons)
async def date_month(callback_query: CallbackQuery, state: FSMContext):
    db_session.global_init("db/my_base.db")
    session = db_session.create_session()
    select_month = callback_query.data
    month_num = months_buttons[select_month][1]
    month_name = months_buttons[select_month][0]
    user_id = callback_query.from_user.id
    user = session.query(User).filter(User.uid == user_id).first()
    timezone = user.timezone

    user_tz = pytz.timezone(timezone)
    now_user = datetime.now(user_tz)
    current_year = now_user.year
    current_month = now_user.month
    current_day = now_user.day
    year_num = current_year
    last_day = monthrange(year_num, month_num)[1]
    last_day_of_month = datetime(year_num, month_num, last_day, 23, 59, 59, tzinfo=user_tz)

    if (year_num < current_year) or \
       (year_num == current_year and month_num < current_month) or \
       (year_num == current_year and month_num == current_month and current_day >= last_day):
        if month_num == 12:
            month_num = 1
            year_num = year_num + 1
        else:
            month_num = month_num + 1
            year_num = year_num + 1
    events_list = []
    for event in session.query(Event).filter(Event.user_id == user_id, Event.year == year_num, Event.month == month_num):
        events_list.append(event.text)
    await state.set_state(Kallend.date_check)
    await state.update_data(month=month_num, year=year_num)
    await callback_query.answer()
    await callback_query.message.answer(f"Ваши события на {month_name} {year_num} года", reply_markup=all_dates if events_list else dates_add_solo)

    session.commit()
    session.close()

@dp.callback_query(F.data == "date_add")
async def date_num(callback: CallbackQuery, state: FSMContext):
    try:
        month = await state.get_data()
        select_month = month.get("month")[:3]
        await callback.answer()
        await callback.message.answer(f"Выберите число {morph.parse(months_buttons[select_month][0][:-1])[0].inflect({'NOUN', 'gent'}).word.capitalize()} {months_buttons[select_month][2]} года", reply_markup=await month_nums(select_month, months_buttons[select_month][1], "add"))
    except NameError:
        await callback.answer()
        await callback.message.answer("Cначала выберите месяц")

@dp.callback_query(lambda call: call.data[-3:] == "add")
async def date_input_add(callback_query: CallbackQuery, state: FSMContext):
    try:
        month = await state.get_data()
        select_month = month.get("month")[:3]
        num = callback_query.data[3:-3]
        await state.update_data(month=str(select_month) + str(num))
        await state.set_state(Kallend.date_add)
        await callback_query.answer()
        today = datetime.now()
        choosed_date = datetime(year=months_buttons[select_month][2], month=list(months_buttons.keys()).index(select_month) + 1, day=int(num))
        if (today - choosed_date).days < 0:
            date_year = months_buttons[select_month][2]
            await callback_query.message.answer(f"Добавьте событие на {num} {morph.parse(months_buttons[select_month][0][:-1])[0].inflect({'NOUN', 'gent'}).word.capitalize()} {date_year} года")
        else:
            date_year = months_buttons[select_month][2] + 1
            await callback_query.message.answer(f"Добавьте событие на {num} {morph.parse(months_buttons[select_month][0][:-1])[0].inflect({'NOUN', 'gent'}).word.capitalize()} {date_year} года")
        await state.update_data(year=date_year)
    except NameError:
        await callback_query.answer()
        await callback_query.message.answer("Cначала выберите месяц")
    
@dp.message(Kallend.date_add)
async def date_add(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(event=message.text)
    data = await state.get_data()
    year = data.get("year")
    month = data.get("month")[:3]
    num = data.get("month")[3:]
    event = data.get("event")
    if num in months_dates[month]:
        if event not in months_dates[month][num][0]:
            months_dates[month][num][0].append(event)
            await message.answer(f"Событие '{event}' успешно добавлено")
        else:
            await message.answer(f"Событие '{event}' уже было добавлено")
    else:
        months_dates[month][num] = [[event], year]
        await message.answer(f"Событие '{event}' успешно добавлено")
    global months_data
    months_data = await state.get_data()
    await message.answer(f"Ваши события на {months_buttons[month][0]} {months_buttons[month][2]} года", reply_markup=all_dates if months_dates[month] else dates_add_solo)
    await state.clear()
     
@dp.callback_query(F.data == "date_del")
async def dates_del(callback: CallbackQuery, state: FSMContext):
    try:
        month = months_data
        select_month = month.get("month")[:3]
        await callback.answer()
        await callback.message.answer(f"Ваши события на {months_buttons[select_month][0][:-1].capitalize()}:\n{'\n'.join([str(day) + ' - ' + ' | '.join(months_dates[select_month][day][0]) for day in months_dates[select_month]])}")
        await callback.message.answer(f"Выберите число {morph.parse(months_buttons[select_month][0][:-1])[0].inflect({'NOUN', 'gent'}).word.capitalize()} для удаления", reply_markup=await month_nums(select_month, months_buttons[select_month][1], "del"))
    except NameError:
        await callback.answer()
        await callback.message.answer("Cначала добавьте событие")

@dp.callback_query(lambda call: call.data[-3:] == "del")
async def date_input_del(callback_query: CallbackQuery, state: FSMContext):
    try:
        month = months_data
        select_month = month.get("month")[:3]
        num = callback_query.data[3:-3]
        await state.update_data(month=str(select_month) + str(num))
        await callback_query.answer()
        events = await inline_events(select_month, num)
        if events:
            await callback_query.message.answer(f"Выберите событие на {num} {morph.parse(months_buttons[select_month][0][:-1])[0].inflect({'NOUN', 'gent'}).word.capitalize()} для удаления", reply_markup=events)
    except NameError:
        await callback.answer()
        await callback.message.answer("Cначала добавьте событие")

@dp.callback_query(lambda call: "dell" in call.data)
async def date_del(callback_query: CallbackQuery, state: FSMContext):
    try:
        data = callback_query.data
        data = data.split("dell")
        event = data[0]
        num = data[1]
        month = months_data
        select_month = month.get("month")[:3]
        months_dates[select_month][num][0].remove(event)
        if not months_dates[select_month][num][0]:
            months_dates[select_month].pop(num)
        await callback_query.answer()
        await callback_query.message.answer(f"Событие '{event}' успешно удалёно")
        await callback_query.message.answer(f"Ваши события на {months_buttons[select_month][0]} {months_buttons[select_month][2]} года", reply_markup=all_dates if months_dates[select_month] else dates_add_solo)
        await state.clear()
    except (NameError, KeyError):
        await callback_query.answer()
        await callback_query.message.answer("Cначала добавьте событие")

@dp.callback_query(F.data == "date_checks")
async def date_checks(callback_query: CallbackQuery, state: FSMContext):
    last_year = 0
    next_year = 0
    for month in months_dates:
        for num in months_dates[month]:
            if last_year == 0:
                last_year = months_dates[month][num][1]
            else:
                if months_dates[month][num][1] != last_year:
                    if last_year > months_dates[month][num][1]:
                        next_year = last_year
                        last_year = months_dates[month][num][1]
                    else:
                        next_year = months_dates[month][num][1]
    await callback_query.answer()
    dates_checks = ''
    if last_year != 0 and next_year == 0:
        dates_checks += str(last_year) + " год:" + "\n"
        for mon in months_dates:
            if months_dates[mon]:
                dates_checks += f"\n{months_buttons[mon][0]}:\n{'\n'.join([str(day) + ' - ' + ' | '.join(months_dates[mon][day][0]) for day in months_dates[mon] if months_dates[mon][day][1] == last_year])}\n"
    elif last_year == 0 and next_year != 0:
        dates_checks += str(next_year) + " год:" + "\n"
        for mon in months_dates:
            if months_dates[mon]:
                dates_checks += f"\n{months_buttons[mon][0]}:\n{'\n'.join([str(day) + ' - ' + ' | '.join(months_dates[mon][day][0]) for day in months_dates[mon] if months_dates[mon][day][1] == next_year])}\n"
    elif last_year != 0 and next_year != 0:
        dates_checks += str(last_year) + " год:" + "\n"
        for mon in months_dates:
            if months_dates[mon]:
                if any(year == last_year for year in [i[1] for i in months_dates[mon].values()]):
                    dates_checks += f"\n{months_buttons[mon][0]}:"
                dates_checks += f"\n{'\n'.join([str(day) + ' - ' + ' | '.join(months_dates[mon][day][0]) for day in months_dates[mon] if months_dates[mon][day][1] == last_year])}\n".rstrip() + "\n"
        dates_checks += "\n" + str(next_year) + " год:" + "\n"
        for mon in months_dates:
            if months_dates[mon]:
                if any(year == next_year for year in [i[1] for i in months_dates[mon].values()]):
                    dates_checks += f"\n{months_buttons[mon][0]}:"
                dates_checks += f"\n{'\n'.join([str(day) + ' - ' + ' | '.join(months_dates[mon][day][0]) for day in months_dates[mon] if months_dates[mon][day][1] == next_year])}\n"
    else:
        await callback_query.message.answer("У вас нет событий")
    await callback_query.message.answer(f"{dates_checks}")
    
@dp.callback_query(F.data == "date_change")
async def date_change(callback_query: CallbackQuery):
    await callback_query.message.answer("Введите месяц >>>", reply_markup=await set_months())

async def month_nums(select_month, last_num, com):
    nums = InlineKeyboardBuilder()
    if com == "add":
        for num in range(1, last_num + 1):
            nums.add(InlineKeyboardButton(text=str(num), callback_data=f"{select_month}{num}add"))
    elif com == "del":
        for num in months_dates[select_month]:
            nums.add(InlineKeyboardButton(text=str(num), callback_data=f"{select_month}{num}del"))
    return nums.adjust(5).as_markup()

async def inline_events(select_month, num):
    try:
        events_for_del = InlineKeyboardBuilder()
        for event in months_dates[select_month][num][0]:
            events_for_del.add(InlineKeyboardButton(text=event, callback_data=f"{event}dell{num}"))
        return events_for_del.adjust(3).as_markup()
    except KeyError:
        await bot.send_message(chat_id=chat_id, text="Cначала добавьте событие")

async def date_checker():
    plans1 = InlineKeyboardBuilder()
    for plan in plans_lst:
        plans1.add(InlineKeyboardButton(text=plan, callback_data=f"{plan}"))
    return plans1.adjust(3).as_markup()
                 
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
