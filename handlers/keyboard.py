from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

SERVICES = {
    "haircut": "Стрижка",
    "beard": "Борода",
    "haircut_beard": "Стрижка + Борода",
}


def get_services_keyboard():
    buttons = []
    for service_id, service_name in SERVICES.items():
        buttons.append(
            [
                InlineKeyboardButton(
                    text=service_name, callback_data=f"service_{service_id}"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


confirm_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить", callback_data="confirm_booking", style="success"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить", callback_data="cancel_booking", style="danger"
            )
        ],
    ]
)
