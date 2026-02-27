import random
import requests
from datetime import datetime, date
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

# Токен от BotFather
TOKEN = "8716783108:AAEKJULDjGs2SAdvWH0v_ilcdV7NiDfMbGo"

# Набор эмодзи для слота
EMOJI_SYMBOLS = ["🍒", "🍋", "🔔", "7️⃣", "💎", "🍀"]

# URL для получения случайных фото котиков
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"

# Словарь для хранения статистики пользователей
user_attempts = {}

def get_main_keyboard():
    """Создаёт клавиатуру с кнопками для команд"""
    keyboard = [
        [KeyboardButton("🎰")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Кнопки подстраиваются под размер экрана
        one_time_keyboard=False  # Клавиатура остаётся после нажатия
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаём клавиатуру
    reply_markup = get_main_keyboard()
    
    await update.message.reply_text(
        "🎰 Добро пожаловать в слот-машину!\n"
        "Нажми 🎰, чтобы запустить барабаны.\n"
        "Если выпадут три одинаковых символа — ты выиграл фото котика! 🐾\n\n"
        "У тебя 15 попыток в день.",
        reply_markup=reply_markup  # Добавляем клавиатуру к сообщению
    )

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    attempts = get_user_attempts(user_id)
    
    if attempts >= 15:
        await update.message.reply_text(
            "❌ У тебя закончились попытки на сегодня!\n"
            "Возвращайся завтра для новых игр! 🕒"
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

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("spin", spin))
    application.run_polling()

if __name__ == "__main__":
    main()
