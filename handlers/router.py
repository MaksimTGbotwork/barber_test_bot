from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from fsm import Booking
from handlers.database import (
    add_booking,
    cancel_booking,
    get_all_bookings,
    get_user_bookings,
)
from handlers.keyboard import SERVICES, confirm_kb, get_services_keyboard

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Добро пожаловать!\n\n"
        "Я помогу вам записаться на услугу.\n\n"
        "/book — записаться\n"
        "/mybookings — мои записи\n"
        "/help — помощь"
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "📋 <b>Список команд:</b>\n\n"
        "✂️ /book — записаться на услугу\n"
        "📅 /mybookings — посмотреть свои записи (и отменить при необходимости)\n"
        "ℹ️ /help — показать это сообщение\n\n"
        "Есть вопросы? Просто напишите нам!",
        parse_mode="HTML",
    )


@router.message(Command("book"))
async def start_booking(message: Message, state: FSMContext):
    await message.answer("Выберите услугу:", reply_markup=get_services_keyboard())
    await state.set_state(Booking.service)


@router.callback_query(Booking.service, F.data.startswith("service_"))
async def process_service(callback: CallbackQuery, state: FSMContext):
    service_id = callback.data.replace("service_", "")
    service_name = SERVICES[service_id]

    await state.update_data(service=service_name)
    await callback.message.answer(
        f"Вы выбрали: {service_name}\n\nТеперь введите желаемую дату (в формате ДД.ММ):"
    )
    await state.set_state(Booking.date)
    await callback.answer()


def validate_date(date_text: str):
    try:
        # добавляем текущий год, раз юзер вводит только ДД.ММ
        current_year = datetime.now().year
        parsed_date = datetime.strptime(
            f"{date_text}.{current_year}", "%d.%m.%Y"
        ).date()
    except ValueError:
        return None  # не смог распарсить — значит формат неправильный

    today = datetime.now().date()
    max_date = today + timedelta(days=30)

    if parsed_date < today:
        return None  # дата в прошлом
    if parsed_date > max_date:
        return None  # слишком далеко

    return parsed_date


@router.message(Booking.date, F.text)
async def process_date(message: Message, state: FSMContext):
    validated_date = validate_date(message.text)

    if validated_date is None:
        await message.answer(
            "Некорректная дата. Введите в формате ДД.ММ (например 15.08), "
            "дата должна быть не раньше сегодня и не позже чем через 30 дней."
        )
        return

    await state.update_data(date=validated_date.strftime("%d.%m.%Y"))
    await message.answer(
        "Отлично! Теперь введите желаемое время (в формате ЧЧ:ММ, например 14:00):"
    )
    await state.set_state(Booking.time)


def validate_time(time_text: str):
    try:
        parsed_time = datetime.strptime(time_text, "%H:%M").time()
    except ValueError:
        return None

    return parsed_time


@router.message(Booking.time, F.text)
async def process_time(message: Message, state: FSMContext):
    validated_time = validate_time(message.text)

    if validated_time is None:
        await message.answer(
            "Некорректное время. Введите в формате ЧЧ:ММ (например 14:00)."
        )
        return

    await state.update_data(time=validated_time.strftime("%H:%M"))

    data = await state.get_data()
    service = data["service"]
    date = data["date"]
    time = data["time"]

    await message.answer(
        f"Проверьте данные записи:\n\n"
        f"Услуга: {service}\n"
        f"Дата: {date}\n"
        f"Время: {time}\n\n"
        f"Всё верно?",
        reply_markup=confirm_kb,
    )


@router.callback_query(F.data == "cancel_booking")
async def process_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Запись отменена❌")
    await callback.answer()


@router.callback_query(F.data == "confirm_booking")
async def process_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await add_booking(
        telegram_id=callback.from_user.id,
        service=data["service"],
        date=data["date"],
        time=data["time"],
    )

    await callback.message.answer("Запись успешно создана! Ждём вас ✅")
    await state.clear()
    await callback.answer()


@router.message(Command("allbookings"))
async def all_bookings(message: Message):
    bookings = await get_all_bookings()

    if not bookings:
        await message.answer("Записей пока нет")
        return

    text = "Все записи:\n\n"
    for telegram_id, service, date, time in bookings:
        text += f"👤 ID: {telegram_id}\n📋 {service} — {date} в {time}\n\n"

    await message.answer(text)


@router.message(Command("mybookings"))
async def my_bookings(message: Message):
    bookings = await get_user_bookings(message.from_user.id)

    if not bookings:
        await message.answer("У вас нет активных записей")
        return

    for booking_id, service, date, time in bookings:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Отменить запись",
                        callback_data=f"delete_{booking_id}",
                        style="danger",
                    )
                ]
            ]
        )
        await message.answer(f"📋 {service} — {date} в {time}", reply_markup=kb)


@router.callback_query(F.data.startswith("delete_"))
async def process_delete_booking(callback: CallbackQuery):
    booking_id = int(callback.data.replace("delete_", ""))
    await cancel_booking(booking_id)
    await callback.message.edit_text("Запись отменена ❌")
    await callback.answer()
