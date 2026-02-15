import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from PIL import Image, ImageFilter, ImageEnhance
import random

BOT_TOKEN = 8397167261:"AAFjgCzvWb7cGeKte-fEfUWZtSUrtA-e7UY"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_photos = {}
user_mode = {}

# 🌟 Главное меню
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🖼 Редактор Фото", callback_data="photo"))
    kb.add(InlineKeyboardButton("🤖 Ассистент", callback_data="ai"))
    return kb

# 🎨 Фото меню с ВАУ-эффектами
def photo_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✨ Улучшить", callback_data="enhance"))
    kb.add(InlineKeyboardButton("🖤 Ч/Б", callback_data="bw"))
    kb.add(InlineKeyboardButton("🌈 Контраст", callback_data="contrast"))
    kb.add(InlineKeyboardButton("💡 Яркость", callback_data="brightness"))
    kb.add(InlineKeyboardButton("🌫 Размытие", callback_data="blur"))
    kb.add(InlineKeyboardButton("🎨 Сепия", callback_data="sepia"))
    kb.add(InlineKeyboardButton("🌅 Винтаж", callback_data="vintage"))
    kb.add(InlineKeyboardButton("🌈 Инверсия", callback_data="invert"))
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))
    return kb

# 🚀 Старт
@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer(
        "Привет 👋\n\nЯ бесплатный Photo + Assistant Bot 😎\nВыбери режим:",
        reply_markup=main_menu()
    )

# 📌 Callback
@dp.callback_query_handler()
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id

    if call.data == "photo":
        user_mode[user_id] = "photo"
        await call.message.edit_text("Отправь фото 📸")

    elif call.data == "ai":
        user_mode[user_id] = "ai"
        await call.message.edit_text("Режим ассистента 🤖")

    elif call.data == "back":
        await call.message.edit_text(
            "Главное меню:",
            reply_markup=main_menu()
        )

    elif call.data in ["enhance","bw","contrast","brightness","blur","sepia","vintage","invert"]:

        if user_id not in user_photos:
            await call.answer("Сначала отправь фото 📸", show_alert=True)
            return

        # 🕹 Прогресс обработки
        msg = await call.message.answer("✨ Обработка: ░░░░░░ 0%")
        for i in range(1,11):
            await asyncio.sleep(0.2)
            progress = "█" * i + "░" * (10-i)
            await msg.edit_text(f"✨ Обработка: {progress} {i*10}%")

        img = Image.open(user_photos[user_id])

        # 🔹 Эффекты
        if call.data == "enhance":
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.8)

        elif call.data == "bw":
            img = img.convert("L")

        elif call.data == "contrast":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)

        elif call.data == "brightness":
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.3)

        elif call.data == "blur":
            img = img.filter(ImageFilter.BLUR)

        elif call.data == "sepia":
            img = img.convert("RGB")
            r, g, b = img.split()
            r = r.point(lambda i: i * 0.9)
            g = g.point(lambda i: i * 0.8)
            b = b.point(lambda i: i * 0.7)
            img = Image.merge("RGB", (r,g,b))

        elif call.data == "vintage":
            img = img.convert("RGB")
            r, g, b = img.split()
            r = r.point(lambda i: i * 0.9)
            g = g.point(lambda i: i * 0.85)
            b = b.point(lambda i: i * 0.7)
            img = Image.merge("RGB", (r,g,b))

        elif call.data == "invert":
            img = Image.eval(img, lambda x: 255 - x)

        new_path = f"edited_{user_id}.jpg"
        img.save(new_path)

        await msg.delete()

        await call.message.answer_photo(
            types.InputFile(new_path),
            reply_markup=photo_menu()
        )

# 🖼 Фото
@dp.message_handler(content_types=['photo'])
async def handle_photo(message: Message):
    user_id = message.from_user.id

    if user_mode.get(user_id) != "photo":
        return

    photo = message.photo[-1]
    path = f"photo_{user_id}.jpg"
    await photo.download(destination_file=path)
    user_photos[user_id] = path

    await message.answer(
        "Фото получено ✅\nВыбери эффект:",
        reply_markup=photo_menu()
    )

# 🤖 Ассистент
@dp.message_handler()
async def assistant(message: Message):
    if user_mode.get(message.from_user.id) != "ai":
        return

    await message.answer(random.choice([
        "Интересно 😏",
        "Хмм 🤔",
        "Согласен 👍",
        "Расскажи подробнее 😉"
    ]))

# ▶️ Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

