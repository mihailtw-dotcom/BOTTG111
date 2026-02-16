import os
import logging
import asyncio
import random
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

API = "https://hltv-api.vercel.app"

subscribers_live = set()
live_messages = {}  # message_id -> match_id
pickem = {}
leaderboard = {}

# ---------------- API ----------------

def get_matches():
    try:
        return requests.get(f"{API}/matches").json()
    except:
        return []

# ---------------- UI ----------------

def header(title="ULTIMATE CYBER LIVE"):
    return f"💎 **{title}** 💎\n\n"

def match_card(match):
    score = match.get('score', 'TBD')
    anim = random.choice(["⚡","💥","✨","🔥"])
    return (
        header("MATCH INFO") +
        f"🎮 {match['team1']} vs {match['team2']} {anim}\n"
        f"🏆 {match['event']}\n"
        f"🎯 Score: {score} {anim*2}\n"
        f"🕒 {match['date']}\n"
    )

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔥 LIVE", callback_data="live"),
        InlineKeyboardButton("📅 Матчи", callback_data="matches"),
        InlineKeyboardButton("🎯 Pick’em", callback_data="pickem"),
        InlineKeyboardButton("📊 Лидерборд", callback_data="leaderboard"),
        InlineKeyboardButton("🚨 LIVE ON/OFF", callback_data="sub_live")
    )
    return kb

# ---------------- START ----------------

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        header() + "😎 **ULTIMATE CYBER LIVE MODE ACTIVE** 😎\n\n"
        "✔ LIVE матчи с динамикой\n"
        "✔ Pick’em с эффектами\n"
        "✔ AI реакции и визуальный интерфейс\n"
        "✔ Лидерборд обновляется в реальном времени",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# ---------------- LIVE ----------------

async def show_live(message):
    matches = get_matches()
    live = [m for m in matches if m["status"] == "live"]
    if not live:
        await message.answer("🚫 LIVE матчей нет")
        return
    for match in live:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🎯 Сделать прогноз", callback_data=f"pick_{match['id']}"))
        sent = await message.answer(match_card(match), parse_mode="Markdown", reply_markup=kb)
        live_messages[sent.message_id] = match['id']

# ---------------- PICK’EM ----------------

@dp.callback_query_handler(lambda c: c.data.startswith("pick_"))
async def pickem_match(call: types.CallbackQuery):
    match_id = call.data.split("_")[1]
    matches = get_matches()
    match = next((m for m in matches if str(m["id"]) == match_id), None)
    if not match:
        await call.answer("Матч не найден 😔")
        return
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton(match['team1'], callback_data=f"choose_{match_id}_{match['team1']}"),
        InlineKeyboardButton(match['team2'], callback_data=f"choose_{match_id}_{match['team2']}")
    )
    await call.message.answer(header("Выбери победителя") + "🎯 Сделай свой выбор:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("choose_"))
async def choose_team(call: types.CallbackQuery):
    _, match_id, team = call.data.split("_")
    user = call.from_user.id
    if user not in pickem:
        pickem[user] = {}
    pickem[user][match_id] = team
    await call.answer(f"✅ Ты выбрал: {team}", show_alert=True)

# ---------------- ЛИДЕРБОРД ----------------

@dp.callback_query_handler(lambda c: c.data == "leaderboard")
async def show_leaderboard(call: types.CallbackQuery):
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    text = header("LEADERBOARD")
    for idx, (user_id, points) in enumerate(sorted_lb[:10], start=1):
        text += f"{idx}. 👤 {user_id} — {points} очков\n"
    await call.message.answer(text, parse_mode="Markdown")

# ---------------- SUB LIVE ----------------

@dp.callback_query_handler(lambda c: c.data == "sub_live")
async def sub_live(call: types.CallbackQuery):
    user_id = call.from_user.id
    if user_id in subscribers_live:
        subscribers_live.remove(user_id)
        await call.answer("❌ LIVE OFF", show_alert=True)
    else:
        subscribers_live.add(user_id)
        await call.answer("✅ LIVE ON", show_alert=True)

# ---------------- ANIMATION ENGINE ----------------

async def animate_live():
    while True:
        await asyncio.sleep(5)
        matches = get_matches()
        live = [m for m in matches if m["status"] == "live"]
        for message_id, match_id in list(live_messages.items()):
            match = next((m for m in live if str(m["id"]) == match_id), None)
            if match:
                try:
                    score = match.get('score', 'TBD')
                    anim = random.choice(["⚡","💥","✨","🔥"])
                    text = (
                        header("LIVE ANIMATION") +
                        f"🎮 {match['team1']} vs {match['team2']} {anim}\n"
                        f"🏆 {match['event']}\n"
                        f"🎯 Score: {score} {anim*2}\n"
                        f"🕒 {match['date']}\n"
                    )
                    await bot.edit_message_text(
                        text, chat_id=list(subscribers_live)[0] if subscribers_live else None, message_id=message_id, parse_mode="Markdown"
                    )
                except:
                    pass

# ---------------- STARTUP ----------------

async def on_startup(dp):
    asyncio.create_task(animate_live())

# ---------------- RUN ----------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
