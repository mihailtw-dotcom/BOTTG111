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

BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_photos = {}
user_edited = {}
user_mode = {}

# 🌟 Главное меню
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🖼 Редактор Фото", callback_data="photo"))
    kb.add(InlineKeyboardButton("🤖 Ассистент", callback_data="ai"))
    kb.add(InlineKeyboardButton("🌤 Инфо", callback_data="info"))
    kb.add(InlineKeyboardButton("🎮 HLTV Матчи", callback_data="matches"))
    return kb

# 🎨 Фото меню
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
    kb.add(InlineKeyboardButton("🖌 Аниме", callback_data="anime"))
    kb.add(InlineKeyboardButton("♻ Сброс", callback_data="reset"))
    kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))
    return kb

# 🔥 HLTV API
def get_matches():
    try:
        url = "https://hltv-api.vercel.app/matches"
        return requests.get(url).json()
    except:
        return []

# 🚀 Старт
@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer(
        "Привет 😎🔥\n\nЯ УЛЬТИМАТИВНЫЙ бот:\n"
        "🖼 Фото / Anime\n"
        "🤖 Ассистент\n"
        "🌤 Погода / Время\n"
        "🎮 HLTV Матчи\n\n"
        "Выбирай:",
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
        await call.message.edit_text("AI режим 🤖")

    elif call.data == "info":
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("⏰ Время", callback_data="time"))
        kb.add(InlineKeyboardButton("🌤 Погода", callback_data="weather"))
        kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))
        await call.message.edit_text("Информация:", reply_markup=kb)

    elif call.data == "matches":
        data = get_matches()

        if not data:
            await call.message.answer("Ошибка HLTV API 😔")
            return

        text = "🎮 Ближайшие матчи:\n\n"

        for m in data[:5]:
            text += f"{m['team1']} vs {m['team2']}\n"
            text += f"🕒 {m['date']}\n"
            text += f"🏆 {m['event']}\n\n"

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🔥 LIVE", callback_data="live"))
        kb.add(InlineKeyboardButton("⬅ Назад", callback_data="back"))

        await call.message.edit_text(text, reply_markup=kb)

    elif call.data == "live":
        data = get_matches()
        live = [m for m in data if m['status'] == "live"]

        if not live:
            await call.message.answer("🚫 Сейчас нет LIVE матчей")
            return

        text = "🔥 LIVE матчи:\n\n"

        for m in live:
            text += f"{m['team1']} vs {m['team2']}\n"
            text += f"🎯 {m.get('score', 'Идёт')}\n\n"

        await call.message.answer(text)

    elif call.data == "back":
        await call.message.edit_text("Главное меню:", reply_markup=main_menu())

    elif call.data == "time":
        now = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        await call.message.answer(f"⏰ Время:\n{now}")

    elif call.data == "weather":
        try:
            weather = requests.get("https://wttr.in/?format=3").text
            await call.message.answer(f"🌤 Погода:\n{weather}")
        except:
            await call.message.answer("Ошибка погоды 😔")

    elif call.data in ["enhance","bw","contrast","brightness","blur","sepia","vintage","invert","anime","reset"]:

        if user_id not in user_photos:
            await call.answer("Сначала фото 📸", show_alert=True)
            return

        if call.data == "reset":
            img_path = user_photos[user_id]
            user_edited[user_id] = img_path
            await call.message.answer_photo(types.InputFile(img_path), reply_markup=photo_menu())
            return

        img_path = user_edited.get(user_id, user_photos[user_id])
        img = Image.open(img_path)

        msg = await call.message.answer("✨ Обработка...")

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
            r,g,b = img.split()
            img = Image.merge("RGB",(r.point(lambda i:i*0.9), g.point(lambda i:i*0.8), b.point(lambda i:i*0.7)))
        elif call.data == "vintage":
            r,g,b = img.split()
            img = Image.merge("RGB",(r.point(lambda i:i*0.9), g.point(lambda i:i*0.85), b.point(lambda i:i*0.7)))
        elif call.data == "invert":
            img = Image.eval(img, lambda x: 255-x)
        elif call.data == "anime":
            img = img.convert("RGB")
            img = img.filter(ImageFilter.CONTOUR)
            img = ImageEnhance.Contrast(img).enhance(1.8)

        edited_path = f"edited_{user_id}.jpg"
        img.save(edited_path)

        user_edited[user_id] = edited_path

        await msg.delete()
        await call.message.answer_photo(types.InputFile(edited_path), reply_markup=photo_menu())

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
    user_edited[user_id] = path

    await message.answer("Фото получено ✅", reply_markup=photo_menu())

# 🤖 AI Ассистент
@dp.message_handler()
async def assistant(message: Message):
    if user_mode.get(message.from_user.id) != "ai":
        return

    await message.answer(random.choice([
        "Интересно 😏",
        "Согласен 👍",
        "Хмм 🤔",
        "Расскажи подробнее 😉"
    ]))

# ▶️ Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
