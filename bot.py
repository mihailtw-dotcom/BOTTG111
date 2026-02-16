import os
import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = os.environ.get("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

HLTV_API = "https://hltv-api.vercel.app/matches"

subscribers_live = set()

# 🔥 Получение матчей
def get_matches():
    try:
        return requests.get(HLTV_API).json()
    except:
        return []

# 🎮 Карточка матча
def match_card(match):
    return (
        f"🎮 **{match['team1']} vs {match['team2']}**\n"
        f"🏆 {match['event']}\n"
        f"🔥 {match['status'].upper()}\n"
        f"🎯 {match.get('score', 'TBD')}\n"
        f"🕒 {match['date']}\n"
    )

# 🌟 Главное меню
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔥 LIVE", callback_data="live"))
    kb.add(InlineKeyboardButton("📅 Матчи", callback_data="matches"))
    kb.add(InlineKeyboardButton("🔔 Подписка LIVE", callback_data="sub_live"))
    return kb

# 🚀 Старт
@dp.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer(
        "😎🔥 **CYBER BOT PRO** 🔥😎\n\n"
        "✔ LIVE матчи\n"
        "✔ Авто-обновление\n"
        "✔ Уведомления\n"
        "✔ Расписание\n\n"
        "Выбирай:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# 🔥 LIVE матчи
@dp.message_handler(commands=['live'])
async def live_matches(message: Message):
    data = get_matches()
    live = [m for m in data if m["status"] == "live"]

    if not live:
        await message.answer("🚫 Сейчас нет LIVE матчей")
        return

    for m in live:
        await message.answer(match_card(m), parse_mode="Markdown")

# 📅 Матчи
@dp.message_handler(commands=['matches'])
async def upcoming_matches(message: Message):
    data = get_matches()

    for m in data[:5]:
        await message.answer(match_card(m), parse_mode="Markdown")

# 🔎 Фильтр по команде
@dp.message_handler(commands=['team'])
async def team_filter(message: Message):
    try:
        team_name = message.text.split()[1].lower()
    except:
        await message.answer("Пример: /team navi")
        return

    data = get_matches()

    filtered = [
        m for m in data
        if team_name in m["team1"].lower()
        or team_name in m["team2"].lower()
    ]

    if not filtered:
        await message.answer("🚫 Матчи не найдены")
        return

    for m in filtered:
        await message.answer(match_card(m), parse_mode="Markdown")

# 🔔 Подписка LIVE
@dp.callback_query_handler(lambda c: c.data == "sub_live")
async def subscribe_live(call: types.CallbackQuery):
    user_id = call.from_user.id

    if user_id in subscribers_live:
        subscribers_live.remove(user_id)
        await call.answer("❌ Подписка отключена", show_alert=True)
    else:
        subscribers_live.add(user_id)
        await call.answer("✅ Подписка на LIVE включена", show_alert=True)

# ▶️ Callback
@dp.callback_query_handler()
async def callbacks(call: types.CallbackQuery):
    if call.data == "live":
        await live_matches(call.message)
    elif call.data == "matches":
        await upcoming_matches(call.message)

# 🚨 LIVE авто-мониторинг
async def live_monitor():
    last_live = set()

    while True:
        await asyncio.sleep(30)  # обновление каждые 30 сек

        matches = get_matches()
        live = [m for m in matches if m["status"] == "live"]

        current_live = set(
            f"{m['team1']} vs {m['team2']}" for m in live
        )

        new_live = current_live - last_live

        if new_live:
            for match in live:
                key = f"{match['team1']} vs {match['team2']}"

                if key in new_live:
                    for user_id in subscribers_live:
                        try:
                            await bot.send_message(
                                user_id,
                                f"🚨 **НОВЫЙ LIVE МАТЧ** 🚨\n\n{match_card(match)}",
                                parse_mode="Markdown"
                            )
                        except:
                            pass

        last_live = current_live

# ▶️ Запуск
async def on_startup(dp):
    asyncio.create_task(live_monitor())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
