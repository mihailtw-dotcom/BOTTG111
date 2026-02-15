import os
import logging
import asyncio
from datetime import datetime
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from PIL import Image, ImageFilter, ImageEnhance
import random

# 🔹 Токен Telegram
BOT_TOKEN = os.environ.get("8397167261:AAFjgCzvWb7cGeKte-fEfUWZtSUrtA-e7UY")  # Вставляется через Secrets Replit

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# 📸 фото
user_photos = {}      # оригинал
user_edited = {}      # текущая версия с эффектами
user_mode = {}        # режим: photo / ai / info

# 🌟 Главное меню
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🖼 Редактор Фото", callback_data="photo"))
    kb.add(InlineKeyboardButton("🤖 Ассистент", callback_data="ai"))
    kb.add(InlineKeyboardButton("🌤 Инфо", callback_data="info"))
    return kb

# 🎨 Фото меню с ВАУ и аниме эффектами
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
    kb.add(InlineKeyboardButton("🖌 Аниме-эффект", callback_data="anime"))
    kb.add(InlineKeyboardButton("♻ Сброс / Удалить эффекты", callback_data="reset"))
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))
    return kb

# 🚀 Старт
@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer(
        "Привет 👋\n\nЯ Photo + Anime + Assistant + Info Bot 😎\nВыбери режим:",
        reply_markup=main_menu()
    )

# 📌 Callback
@dp.callback_query_handler()
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id

    # --- Фото ---
    if call.data == "photo":
        user_mode[user_id] = "photo"
        await call.message.edit_text("Отправь фото 📸")

    # --- Ассистент ---
    elif call.data == "ai":
        user_mode[user_id] = "ai"
        await call.message.edit_text("Режим ассистента 🤖")

    # --- Инфо ---
    elif call.data == "info":
        user_mode[user_id] = "info"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⏰ Текущее время", callback_data="time"))
        kb.add(InlineKeyboardButton("🌤 Погода", callback_data="weather"))
        kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))
        await call.message.edit_text("Выбери инфо:", reply_markup=kb)

    # --- Назад ---
    elif call.data == "back":
        await call.message.edit_text("Главное меню:", reply_markup=main_menu())

    # --- Фото эффекты ---
    elif call.data in ["enhance","bw","contrast","brightness","blur","sepia","vintage","invert","anime","reset"]:
        if user_id not in user_photos:
            await call.answer("Сначала отправь фото 📸", show_alert=True)
            return

        if call.data == "reset":
            # сбросить на оригинал
            edited_path = user_photos[user_id]
            user_edited[user_id] = edited_path
            await call.message.answer_photo(types.InputFile(edited_path), reply_markup=photo_menu())
            return

        # берём текущую версию
        img_path = user_edited.get(user_id, user_photos[user_id])
        img = Image.open(img_path)

        # прогресс
        msg = await call.message.answer("✨ Обработка: ░░░░░░ 0%")
        for i in range(1,11):
            await asyncio.sleep(0.2)
            progress = "█" * i + "░" * (10-i)
            await msg.edit_text(f"✨ Обработка: {progress} {i*10}%")

        # применяем эффект
        if call.data == "enhance":
            img = ImageEnhance.Sharpness(img).enhance(1.8)
        elif call.data == "bw":
            img = img.convert("L")
        elif call.data == "contrast":
            img = ImageEnhance.Contrast(img).enhance(1.5)
        elif call.data == "brightness":
            img = ImageEnhance.Brightness(img).enhance(1.3)
        elif call.data == "blur":
            img = img.filter(ImageFilter.BLUR)
        elif call.data == "sepia":
            r, g, b = img.split()
            img = Image.merge("RGB", (r.point(lambda i:i*0.9), g.point(lambda i:i*0.8), b.point(lambda i:i*0.7)))
        elif call.data == "vintage":
            r, g, b = img.split()
            img = Image.merge("RGB", (r.point(lambda i:i*0.9), g.point(lambda i:i*0.85), b.point(lambda i:i*0.7)))
        elif call.data == "invert":
            img = Image.eval(img, lambda x: 255 - x)
        elif call.data == "anime":
            img = img.convert("RGB")
            img = img.filter(ImageFilter.CONTOUR)
            img = ImageEnhance.Contrast(img).enhance(1.8)
            img = ImageEnhance.Brightness(img).enhance(1.4)

        # сохраняем текущую версию
        edited_path = f"edited_{user_id}.jpg"
        img.save(edited_path)
        user_edited[user_id] = edited_path

        await msg.delete()
        await call.message.answer_photo(types.InputFile(edited_path), reply_markup=photo_menu())

    # --- Инфо ---
    elif call.data == "time":
        now = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        await call.message.answer(f"⏰ Текущее время:\n{now}")
    elif call.data == "weather":
        url = "https://wttr.in/?format=3"
        try:
            resp = requests.get(url)
            await call.message.answer(f"🌤 Погода:\n{resp.text}")
        except:
            await call.message.answer("Ошибка получения погоды 😔")

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
    user_edited[user_id] = path  # стартовая версия
    await message.answer("Фото получено ✅\nВыбери эффект:", reply_markup=photo_menu())

# 🤖 Ассистент
@dp.message_handler()
async def assistant(message: Message):
    if user_mode.get(message.from_user.id) != "ai":
        return
    await message.answer(random.choice([
        "Интересно 😏", "Хмм 🤔", "Согласен 👍", "Расскажи подробнее 😉"
    ]))

# ▶️ Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
