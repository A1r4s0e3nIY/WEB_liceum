import asyncio
import pymorphy3
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.types import CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
from geopy import geocoders


bot = Bot("8573629235:AAFkezNHEOOT8ZxsyysACPPmrGu65LwSOwY", proxy="datacloud-tech.org") 

dp = Dispatcher()

chat_id = None

sutc = 0

class Plans(StatesGroup):
    plan_add = State()
    plan_del = State()

class Reg(StatesGroup):
    time_input = State()

class Kallend(StatesGroup):
    date_add = State()
    date_del = State()
    date_check = State()
    date_month = State()
    time_check = State()

morph = pymorphy3.MorphAnalyzer()
months_dates = {"jan": {}, "feb": {}, "mar": {}, "apr": {}, "may": {}, "jun": {}, "jul": {}, "aug": {}, "sep": {}, "ocr": {}, "nov": {}, "dec": {}}
months_buttons = {"jan": ["Январь❄", 31, 2026], "feb": ["Февраль❄", 28, 2026], "mar": ["Март🌸", 31, 2026], "apr": ["Апрель🌸", 30, 2025], "may": ["Май🌸", 31, 2025], "jun": ["Июнь☀", 30, 2025],
                  "jul": ["Июль☀", 31, 2025], "aug": ["Август☀", 31, 2025], "sep": ["Сентябрь🍁", 30, 2025], "ocr": ["Октябрь🍁", 31, 2025], "nov": ["Ноябрь🍁", 30, 2025], "dec": ["Декабрь❄", 31, 2025]}


main_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Планы на день")], [KeyboardButton(text="Календарь")]], resize_keyboard=True)
start_menu = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Открыть меню", callback_data="main_menu")]])
start_menu_bt = InlineKeyboardButton(text="Открыть меню 📑 ", callback_data="main_menu")
plans_add = InlineKeyboardButton(text="Добавить план✅ ", callback_data="plan_add")
plans_del = InlineKeyboardButton(text="Удалить план❌ ", callback_data="plan_del")
plans_check = InlineKeyboardButton(text="Посмотреть план 👀 ", callback_data="plan_check")
all_plans = InlineKeyboardMarkup(inline_keyboard=[[plans_add], [plans_del], [plans_check], [start_menu_bt]])
plans_add_solo = InlineKeyboardMarkup(inline_keyboard=[[plans_add], [start_menu_bt]])
dates_add = InlineKeyboardButton(text="Добавить дату✅ ", callback_data="date_add")
dates_del = InlineKeyboardButton(text="Удалить дату❌ ", callback_data="date_del")
all_checks = InlineKeyboardButton(text="Посмотреть все даты 👀", callback_data="date_checks")
dates_change = InlineKeyboardButton(text="Изменить месяц↩ ", callback_data="date_change")
all_dates = InlineKeyboardMarkup(inline_keyboard=[[dates_add], [dates_del], [all_checks], [dates_change], [start_menu_bt]])
dates_add_solo = InlineKeyboardMarkup(inline_keyboard=[[dates_add], [dates_change], [start_menu_bt]])
start_reg = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Начать регистрацию📃", callback_data="start_reg")]])
geopos_select = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Ваше местоположение❓", callback_data="pos_select")]])
geoposition = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Калининград", callback_data="Калининград")], 
                                                    [InlineKeyboardButton(text="Москва", callback_data="Москва")], 
                                                    [InlineKeyboardButton(text="Самара", callback_data="Самара")], 
                                                    [InlineKeyboardButton(text="Екатеринбург", callback_data="Екатеринбург")], 
                                                    [InlineKeyboardButton(text="Омск", callback_data="Омск")], 
                                                    [InlineKeyboardButton(text="Новосибирск", callback_data="Новосибирск")], 
                                                    [InlineKeyboardButton(text="Иркутск", callback_data="Иркутск")], 
                                                    [InlineKeyboardButton(text="Якутск", callback_data="Якутск")], 
                                                    [InlineKeyboardButton(text="Владивосток", callback_data="Владивосток")], 
                                                    [InlineKeyboardButton(text="Дружина", callback_data="Дружина")], 
                                                    [InlineKeyboardButton(text="Петропавловск-Камчатский", callback_data="Петропавловск-Камчатский")]])

@dp.message(CommandStart())
async def start(message: Message):
    chat_id = message.chat.id
    con = sqlite3.connect("my_base.db")
    cur = con.cursor()
    sid = message.from_user.id
    sname = message.from_user.first_name
    res = cur.execute("""SELECT id FROM Users WHERE id = ? LIMIT 1""", [sid]).fetchall()
    if not res:
        await message.answer(f"Привет, {message.from_user.first_name}! В этом боте собраны все полезные функции для твоей ежедневной рутины.\nВы не зарегистрированы в системе - начните регистрацию:", reply_markup=start_reg)
        result = cur.execute("INSERT INTO Users(id, name) VALUES(?, ?)", [sid, sname])
    else:
        await message.answer(f"Привет, {message.from_user.first_name}! В этом боте собраны все полезные функции для твоей ежедневной рутины", reply_markup=start_menu)
    con.commit()
    con.close()

@dp.callback_query(F.data == "start_reg")
async def registration(Callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.time_input)
    await callback_query.answer(f"Укажите ваш город.\nЕсли Вы живете не в городе, или города, в котором Вы живете, нет, выберите ближайший к вам город из списка.", reply_markup=geoposition)
    data = callback_query.data
    gn = geopy.geocoders.GeoNames(username='имя учётной записи')
    loc = gn.geocode(data)
    loc_tz = gn.reverse_timezone(loc.point)
    dt_UTC = datetime(2020, 11, 27, 12, 0, 0, tzinfo=timezone.utc)
    sutc = dt_UTC.astimezone(loc_tz.pytz_timezone)
    print(sutc)


@dp.callback_query(F.data == "main_menu")
async def menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Вы в меню")
    await callback.message.answer("Добро пожаловать!", reply_markup=main_menu)

@dp.message(F.text == "Планы на день")
async def plans(message: Message, state: FSMContext):
    await state.clear()
    con = sqlite3.connect("my_base.db")
    cur = con.cursor()
    sid = message.from_user.id
    plans = cur.execute("""SELECT plans FROM Users WHERE id = ? LIMIT 1""", [sid]).fetchone()
    plans_str = plans[0]
    plans_list = plans_str.split("\n") if plans_str else []
    await message.answer(f"Вы в меню планов", reply_markup=all_plans if len(plans_list) else plans_add_solo)

@dp.callback_query(F.data == "plan_add")
async def plans_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Plans.plan_add)
    await callback.answer()
    await callback.message.answer("Введите ваш план")

async def inline_plans(sid):
    con = sqlite3.connect("my_base.db")
    cursor = con.cursor()
    result = cursor.execute("SELECT plans FROM Users WHERE id = ?", (sid,)).fetchone()
    plans_str = result[0]
    plans_list = plans_str.split("\n") if plans_str else []
    plans_for_del = InlineKeyboardBuilder()
    for plan in plans_list:
        plans_for_del.add(InlineKeyboardButton(text=plan, callback_data=f"{plan}"))
    return plans_for_del.adjust(3).as_markup()
    
@dp.callback_query(F.data == "plan_del")
async def plans_del(callback: CallbackQuery, state: FSMContext):
    sid = callback.from_user.id
    await state.set_state(Plans.plan_del)
    await callback.answer()
    await callback.message.answer("Выберите план для удаления", reply_markup=await inline_plans(sid))
    
@dp.message(Plans.plan_add)
async def plan_add(message: Message, state: FSMContext):
    plan_text = message.text
    
    con = sqlite3.connect("my_base.db")
    cur = con.cursor()
    sid = message.from_user.id
    cur.execute("SELECT plans FROM Users WHERE id = ?", (sid,))
    result = cur.fetchone()

    if result and result[0]:
        current_plans = result[0]
        new_plans = current_plans + "\n" + plan_text #планы пользователя через "\n" 
    else:
        new_plans = plan_text
    cur.execute("""
        UPDATE Users 
        SET plans = ? 
        WHERE id = ?
    """, (new_plans, sid)) #обновление списка планов
    con.commit()
    con.close()
    await message.answer(f"План '{plan_text}' успешно добавлен")
    await message.answer("Вы в меню планов", reply_markup=all_plans)
    await state.clear()

@dp.callback_query(Plans.plan_del)
async def plan_del(callback_query: CallbackQuery, state: FSMContext): 
    plan = callback_query.data
    sid = callback_query.from_user.id
    con = sqlite3.connect("my_base.db")
    cursor = con.cursor()
    plans = cursor.execute("SELECT plans FROM Users WHERE id = ?", (sid,)).fetchone()
    plans_str = plans[0]
    plans_list = plans_str.split("\n") if plans_str else []
    plans_list.remove(plan)
    new_plans_str = "\n".join(plans_list)
    cursor.execute("UPDATE Users SET plans = ? WHERE id = ?", (new_plans_str, sid))
    con.commit()
    con.close()
    await state.clear()
    await callback_query.answer()
    await callback_query.message.answer(f"План '{plan}' успешно удалён")
    await callback_query.message.answer(f"Вы в меню планов", reply_markup=all_plans if plans_list else plans_add_solo)

@dp.callback_query(F.data == "plan_check")
async def plans_check(callback_query: CallbackQuery):
    sid = callback_query.from_user.id
    con = sqlite3.connect("my_base.db")
    cursor = con.cursor()
    plans = cursor.execute("SELECT plans FROM Users WHERE id = ?", (sid,)).fetchone()
    await callback_query.answer()
    await callback_query.message.answer(f"Ваши планы на сегодня:\n{plans[0]}", reply_markup=all_plans)
    
@dp.message(F.text == "Календарь")
async def kallen(message: Message, state: FSMContext):
    await message.answer("Введите месяц >>>", reply_markup=await set_months())


@dp.callback_query(lambda call: call.data in months_buttons)
async def date_month(callback_query: CallbackQuery, state: FSMContext):
    select_month = callback_query.data
    await state.set_state(Kallend.date_check)
    await state.update_data(month=select_month)
    await callback_query.answer()
    await callback_query.message.answer(f"Ваши события на {" ".join([str(i) for i in months_buttons[select_month][::2]])} года", reply_markup=all_dates if months_dates[select_month] else dates_add_solo)

@dp.callback_query(F.data == "date_add")
async def date_num(callback: CallbackQuery, state: FSMContext):
    try:
        month = await state.get_data()
        if not month:
            month = months_data
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
        if not month:
            month = months_data
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
    global chat_id
    chat_id = message.chat.id
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

async def set_months():
    months = InlineKeyboardBuilder()
    months.add(InlineKeyboardButton(text=months_buttons["dec"][0], callback_data=f"dec"))
    december = months_buttons.pop("dec")
    for month in months_buttons:
        months.add(InlineKeyboardButton(text=months_buttons[month][0], callback_data=f"{month}"))
    months.add(start_menu_bt)
    for month in months_buttons:
        if len(months_dates[month]) != 0:
            months.add(all_checks)
            break
    months_buttons["dec"] = december
    return months.adjust(3).as_markup()

async def notify_users():
    while True:
        if any(months_dates.values()):
            today = datetime.now()
            for month in months_dates:
                for num in months_dates[month]:
                    for event in months_dates[month][num][0]:
                        event_date = datetime(year=months_dates[month][num][1], month=list(months_buttons.keys()).index(month.lower()) + 1, day=int(num))
                        if (event_date - today).total_seconds() / 60 <= 0:
                            try:
                                await bot.send_message(chat_id=chat_id, text=f"Наступило событие: {event}")
                                months_dates[month][num][1] += 1
                            except Exception as e:
                                await bot.send_message(chat_id=chat_id, text="Пройдите регистрацию для получения уведомлений /reg")
            await asyncio.sleep(300)
        else:
            await asyncio.sleep(30)

async def change_year():
    while True:
        today = datetime.now()
        for month in months_buttons:
            month_date = datetime(year=months_buttons[month][2], month=list(months_buttons.keys()).index(month) + 1, day=months_buttons[month][1])
            if (today - month_date).days >= 1:
                months_buttons[month][2] += 1
        await asyncio.sleep(86400)

async def change_feb():
    if datetime.now().year % 4 == 0:
        months_buttons["feb"][1] = 29
    else:
        if 29 in months_dates["feb"]:
            months_dates["feb"].pop(29)
    asyncio.sleep(86400)
                 
async def main():
    asyncio.create_task(change_year())
    asyncio.create_task(notify_users())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
