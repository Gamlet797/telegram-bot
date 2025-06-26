from aiogram import Bot, Dispatcher, types, executor
import logging
import requests

# Токен основного бота
API_TOKEN = '7863328224:AAGsA6QAOcJ5MyfEOl2Ri17wW5tS_Su-fPM'

# ID администратора (куда приходят уведомления)
ADMIN_ID = 442635815

# Второй бот (для уведомлений)
SECOND_BOT_TOKEN = "8006311746:AAGVsOpd67wjQrRAnbh7aXspYKlZvWQK0ns"
SECOND_BOT_CHAT_ID = 442635815  # Можешь заменить на ID группы/канала

# Инициализация
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Храним состояние пользователей
state = {}

# Каталог услуг
services = {
    "Икра черная 1 кг": 67000,
    "Икра красная горбуша 1 кг": 12000,
    "Икра красная кета 1 кг": 12000,
    "Икра красная нерка 1 кг": 12000,
    "Отвезти Вискаса в грумминг (Мойка, сушка, вычесывание)": 3000,
    "Впустить Элису": 0,
    "Почистить холодильник перед отъездом": 0,
    "Найти мать/успокоить мать — 2 билета в Ikra/Tajiri go": 40000
}

# Реквизиты
payment_info = (
    "💳 Оплата по реквизитам:\n\n"
    "1. СБП: +7 985 146 75 27 — Ложинский Максим Романович (Т-БАНК)\n"
    "2. Карта: 5536 9139 7159 7972\n"
    "3. Крипта (TRC20): TXb9zuap4hK37HWQFGmugWLrUftwd3b3JA\n\n"
    "❗ После оплаты нажмите «Я оплатил» и оставьте комментарий к заказу."
)

# Функция уведомления через второго бота
def notify_via_second_bot(text):
    url = f"https://api.telegram.org/bot{SECOND_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": SECOND_BOT_CHAT_ID,
        "text": text
    }
    requests.post(url, data=data)

# Генерация главного меню
def get_main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for name in services:
        keyboard.add(name)
    return keyboard

# Команда /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Добро пожаловать! Выберите услугу:", reply_markup=get_main_menu())

# Выбор услуги
@dp.message_handler(lambda message: message.text in services)
async def select_service(message: types.Message):
    state[message.from_user.id] = {
        "service": message.text,
        "price": services[message.text],
        "step": "payment"
    }
    pay_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    pay_keyboard.add("Я оплатил", "Отменить заказ")
    await message.answer(
        f"Вы выбрали: {message.text}\nСтоимость: {services[message.text]} ₽\n\n{payment_info}",
        reply_markup=pay_keyboard
    )

# Отмена заказа
@dp.message_handler(lambda message: message.text == "Отменить заказ")
async def cancel_order(message: types.Message):
    state.pop(message.from_user.id, None)
    await message.answer("❌ Заказ отменён. Выберите услугу:", reply_markup=get_main_menu())

# После нажатия "Я оплатил"
@dp.message_handler(lambda message: state.get(message.from_user.id, {}).get("step") == "payment" and message.text == "Я оплатил")
async def ask_comment(message: types.Message):
    state[message.from_user.id]["step"] = "comment"
    await message.answer("Добавьте комментарий к заказу (адрес, пожелания и т.д.):", reply_markup=types.ReplyKeyboardRemove())

# Получение комментария и отправка заказа
@dp.message_handler(lambda message: state.get(message.from_user.id, {}).get("step") == "comment")
async def confirm_payment(message: types.Message):
    user_state = state.get(message.from_user.id, {})
    text = (
        f"🆕 Новый заказ!\n\n"
        f"👤 Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"📦 Услуга: {user_state.get('service')}\n"
        f"💰 Сумма: {user_state.get('price')} ₽\n"
        f"💬 Комментарий: {message.text}"
    )

    await bot.send_message(ADMIN_ID, text)
    notify_via_second_bot(text)

    await message.answer("Ваш заказ отправлен администратору ✅")
    state.pop(message.from_user.id, None)
    await message.answer("Выберите услугу:", reply_markup=get_main_menu())

# Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
