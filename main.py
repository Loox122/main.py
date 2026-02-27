import random
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes

# Токен от BotFather
TOKEN = "8716783108:AAEKJULDjGs2SAdvWH0v_ilcdV7NiDfMbGo"

# Набор эмодзи для слота
EMOJI_SYMBOLS = ["🍒", "🍋", "🔔", "7️⃣", "💎", "🍀"]

# URL для получения случайных фото котиков
CAT_API_URL = "https://api.thecatapi.com/v1/images/search"

def get_main_keyboard():
    """Создаёт клавиатуру с кнопками для команд"""
    keyboard = [
        [KeyboardButton("/start"), KeyboardButton("/spin")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Кнопки подстраиваются под размер экрана
        one_time_keyboard=False  # Клавиатура остаётся после нажатия
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Создаём клавиатуру
    reply_markup = get_main_keyboard()
    
    await update.message.reply_text(
        "🎰 Добро пожаловать в слот-машину!\n"
        "Нажми /spin, чтобы запустить барабаны.\n"
        "Если выпадут три одинаковых символа — ты выиграл фото котика! 🐾",
        reply_markup=reply_markup  # Добавляем клавиатуру к сообщению
    )

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Выбираем 3 случайных эмодзи
    result = [random.choice(EMOJI_SYMBOLS) for _ in range(3)]
    
    # Формируем строку с результатом
    result_text = " | ".join(result)
    
    # Отправляем результат
    await update.message.reply_text(f"🎰 {result_text} 🎰")
    
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
        await update.message.reply_text("Увы, не повезло. Попробуй ещё раз! /spin")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("spin", spin))
    application.run_polling()

if __name__ == "__main__":
    main()
