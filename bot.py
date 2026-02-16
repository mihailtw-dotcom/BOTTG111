import os
import logging
import asyncio
import random
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

API = "https://hltv-api.vercel.app"

subscribers_live = set()
live_messages = {}  # message_id -> match_id

# ---------------- API ----------------

def get_matches():
    try:
        return requests.get(f"{API}/matches").json()
    except:
        return []

def get_teams():
    try:
        return requests.get(f"{API}/teams").json()
    except:
        return []

def get_players():
    try:
        return requests.get(f"{API}/players").json()
    except:
        return []

# ---------------- UI ----------------

def header(title="CYBER ESPORTS PLATFORM"):
    return f"💎 **{title}** 💎\n\n"

def match_card(match):
    return (
        header("MATCH INFO") +
        f"🎮 **{match['team1']} vs {match['team2']}**\n"
        f"🏆 {match['event']}\n"
        f"🔥 Status: {match['status'].upper()}\n"
        f"🎯 Score: {match.get('score', 'TBD')}\n"
        f"🕒 {match['date']}\n"
    )

def team_card(team):
    return (
        header("TEAM INFO") +
        f"🏆 **{team['name']}**\n"
        f"🌍 {team['country']}\n"
        f"📊 Rank: #{team.get('rank', 'N/A')}\n"
    )

def player_card(player):
    return (
        header("PLAYER INFO") +
        f"🎯 **{player['name']}**\n"
        f"👤 Team: {player['team']}\n"
        f"🌍 {player['country']}\n"
    )

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔥 LIVE", callback_data="live"),
        InlineKeyboardButton("📅 Матчи", callback_data="matches"),
        InlineKeyboardButton("🏆 Команды", callback_data="teams"),
        InlineKeyboardButton("🎯 Игроки", callback_data="players"),
        InlineKeyboardButton("😈 Предсказание", callback_data="predict"),
        InlineKeyboardButton("🚨 LIVE ON/OFF", callback_data="sub_live")
    )
    return kb

# ---------------- START ----------------

@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer(
        header() +
        "😎 **PLATFORM ONLINE** 😎\n\n"
        "✔ LIVE матчи\n"
        "✔ Рейтинг команд и игроков\n"
        "✔ AI прогнозы\n"
        "✔ Кибер-интерфейс",
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
        kb.add(InlineKeyboardButton("🎮 Детали", callback_data=f"match_{match['id']}"))
        sent = await message.answer(match_card(match), parse_mode="Markdown", reply_markup=kb)
        live_messages[sent.message_id] = match['id']

# ---------------- MATCH DETAILS ----------------

@dp.callback_query_handler(lambda c: c.data.startswith("match_"))
async def match_details(call: types.CallbackQuery):
    match_id = call.data.split("_")[1]
    matches = get_matches()
    match = next((m for m in matches if str(m["id"]) == match_id), None)
    if not match:
        await call.answer("Матч не найден 😔")
        return
    await call.message.answer(match_card(match), parse_mode="Markdown")

# ---------------- MATCHES ----------------

async def show_matches(message):
    matches = get_matches()
    for match in matches[:5]:
        await message.answer(match_card(match), parse_mode="Markdown")

# ---------------- TEAMS ----------------

async def show_teams(message):
    teams = get_teams()
    for team in teams[:10]:
        await message.answer(team_card(team), parse_mode="Markdown")

# ---------------- PLAYERS ----------------

async def show_players(message):
    players = get_players()
    for player in players[:10]:
        await message.answer(player_card(player), parse_mode="Markdown")

# ---------------- PREDICTION ----------------

async def predict_match(message):
    matches = get_matches()
    upcoming = [m for m in matches if m["status"] == "upcoming"]
    if not upcoming:
        await message.answer("🚫 Нет матчей для предсказания")
        return
    match = random.choice(upcoming)
    winner = random.choice([match['team1'], match['team2']])
    confidence = random.randint(55, 95)
    await message.answer(
        header("AI PREDICTION") +
        f"🎮 {match['team1']} vs {match['team2']}\n\n"
        f"🏆 Победитель: **{winner}**\n"
        f"📊 Уверенность AI: {confidence}%",
        parse_mode="Markdown"
    )

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

# ---------------- CALLBACKS ----------------

@dp.callback_query_handler()
async def callbacks(call: types.CallbackQuery):
    if call.data == "live":
        await show_live(call.message)
    elif call.data == "matches":
        await show_matches(call.message)
    elif call.data == "teams":
        await show_teams(call.message)
    elif call.data == "players":
        await show_players(call.message)
    elif call.data == "predict":
        await predict_match(call.message)

# ---------------- NEURAL AI CHAT ----------------

@dp.message_handler()
async def neural_ai(message: Message):
    text = message.text.lower()
    responses = [
        "😎 AI анализирует...",
        "🧠 Прогноз обрабатывается...",
        "😈 Интересный запрос...",
        "🔥 Кибер-данные готовы"
    ]
    if "привет" in text:
        await message.answer("😎 Yo, игрок")
    elif "кто выиграет" in text:
        await predict_match(message)
    elif "live" in text:
        await show_live(message)
    else:
        await message.answer(random.choice(responses))

# ---------------- LIVE MONITOR ----------------

async def live_monitor():
    last_live = set()
    while True:
        await asyncio.sleep(30)
        matches = get_matches()
        live = [m for m in matches if m["status"] == "live"]
        current_live = set(f"{m['team1']} vs {m['team2']}" for m in live)
        new_live = current_live - last_live
        if new_live:
            for match in live:
                key = f"{match['team1']} vs {match['team2']}"
                if key in new_live:
                    for user_id in subscribers_live:
                        try:
                            await bot.send_message(user_id, match_card(match), parse_mode="Markdown")
                        except:
                            pass
        last_live = current_live

# ---------------- STARTUP ----------------

async def on_startup(dp):
    asyncio.create_task(live_monitor())

# ---------------- RUN ----------------

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
