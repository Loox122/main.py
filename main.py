import random
import requests
from datetime import date
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes
import time

# Токен от BotFather
TOKEN = "8716783108:AAEKJULDjGs2SAdvWH0v_ilcdV7NiDfMbGo"

# Набор эмодзи для слота
EMOJI_SYMBOLS = ["🍒", "🍋", "🔔", "7️⃣", "💎", "🍀"]

# URL для получения случайных фото котиков
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"

# Словарь для хранения статистики пользователей
user_attempts = {}
# Словарь для хранения времени последнего спина пользователя
last_spin_time = {}
# Словарь для хранения времени последнего запроса проверки попыток
last_check_time = {}

# Задержка между действиями в секундах
ACTION_COOLDOWN = 3

def get_keyboard_for_user(user_id):
    """Создаёт клавиатуру с учётом количества попыток пользователя"""
    attempts = get_user_attempts(user_id)

    if attempts >= 15:
        # Если попыток нет — не показываем кнопку /spin
        keyboard = [
            [KeyboardButton("Проверить количество попыток")]
        ]
    else:
        # Если попытки есть — показываем кнопку /spin
        keyboard = [
            [KeyboardButton("/spin")]
        ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

def get_user_attempts(user_id):
    """Получает количество попыток пользователя за текущий день"""
    today = date.today()
    user_data = user_attempts.get(user_id, {})

    if user_data.get('date') == today:
        return user_data['attempts']
    else:
        # Если это новый день, сбрасываем счётчик
        user_attempts[user_id] = {'date': today, 'attempts': 0}
        return 0

def increment_user_attempts(user_id):
    """Увеличивает количество попыток пользователя"""
    today = date.today()
    if user_id not in user_attempts or user_attempts[user_id]['date'] != today:
        user_attempts[user_id] = {'date': today, 'attempts': 1}
    else:
        user_attempts[user_id]['attempts'] += 1

def can_spin(user_id):
    """Проверяет, может ли пользователь сделать спин (с учётом задержки)"""
    current_time = time.time()
    last_time = last_spin_time.get(user_id, 0)
    time_passed = current_time - last_time

    if time_passed < ACTION_COOLDOWN:
        return False
    else:
        last_spin_time[user_id] = current_time
        return True

def can_check(user_id):
    """Проверяет, может ли пользователь проверить количество попыток (с учётом задержки)"""
    current_time = time.time()
    last_time = last_check_time.get(user_id, 0)
    time_passed = current_time - last_time

    if time_passed < ACTION_COOLDOWN:
        return False
    else:
        last_check_time[user_id] = current_time
        return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Создаём клавиатуру с учётом текущего статуса пользователя
    reply_markup = get_keyboard_for_user(user_id)

    await update.message.reply_text(
        "🎰 Добро пожаловать в слот-машину!\n"
        "Нажми /spin, чтобы запустить барабаны.\n"
        "Если выпадут три одинаковых символа — ты выиграл фото котика! 🐾\n\n"
        "У тебя 15 попыток в день.",
        reply_markup=reply_markup
    )

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Проверяем, не спамит ли пользователь
    if not can_spin(user_id):
        # Просто игнорируем команду без ответа
        return

    attempts = get_user_attempts(user_id)
    if attempts >= 15:
        await update.message.reply_text(
            "❌ У тебя закончились попытки на сегодня!\n"
            "Возвращайся завтра для новых игр! 🕒",
            reply_markup=get_keyboard_for_user(user_id) # Обновляем клавиатуру
        )
        return

    # Увеличиваем счётчик попыток
    increment_user_attempts(user_id)
    remaining_attempts = 15 - attempts - 1

    # Выбираем 3 случайных эмодзи
    result = [random.choice(EMOJI_SYMBOLS) for _ in range(3)]

    # Формируем строку с результатом
    result_text = " | ".join(result)

    # Отправляем результат
    message_text = f"🎰 {result_text} 🎰\n"
    message_text += f"Осталось попыток: {remaining_attempts}"

    await update.message.reply_text(message_text)

    # Проверяем выигрыш
    if result[0] == result[1] == result[2]:
        # Получаем случайное фото котика
        try:
            response = requests.get(CAT_API_URL)
            if response.status_code == 200:
                cat_data = response.json()
                cat_url = cat_data[0]["url"]
                await update.message.reply_photo(
                    photo=cat_url,
                    caption="🎉 ПОБЕДА! Вот твой приз — котик! 🐾"
                )
            else:
                await update.message.reply_text("🎉 ПОБЕДА! Но фото котика не загрузилось. Попробуй ещё раз!")
        except Exception as e:
            print(f"Ошибка при загрузке фото: {e}")
            await update.message.reply_text("🎉 ПОБЕДА! Но фото котика не загрузилось. Попробуй ещё раз!")
    else:
        await update.message.reply_text("Увы, не повезло. Попробуй ещё раз!")

    # Обновляем клавиатуру после спина
    await update.message.reply_text(
        f"Осталось попыток: {remaining_attempts}",
        reply_markup=get_keyboard_for_user(user_id)
    )

async def check_attempts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для кнопки 'Проверить количество попыток'"""
    user_id = update.effective_user.id

    # Проверяем, не спамит ли пользователь с проверкой
    if not can_check(user_id):
        # Просто игнорируем запрос без ответа
        return

    attempts = get_user_attempts(user_id)
    remaining = max(0, 15 - attempts)

    if remaining > 0:
        message = f"✅ У тебя ещё есть {remaining} попыток! Используй /spin!"
    else:
        message = "❌ Попыток нет. Новые попытки появятся завтра."

    # Всегда обновляем клавиатуру — она покажет актуальное состояние
    await update.message.reply_text(
        message,
        reply_markup=get_keyboard_for_user(user_id)
    )

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("spin", spin))

    # Добавляем обработчик для текстового сообщения «Проверить количество попыток»
    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(
        filters.Text("Проверить количество попыток"),
        check_attempts
    ))

    application.run_polling()

if __name__ == "__main__":
    main()

