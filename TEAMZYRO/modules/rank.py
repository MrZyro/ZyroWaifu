# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters, enums  
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import random
import asyncio
import html
from TEAMZYRO import app as Client
from TEAMZYRO import user_collection, top_global_groups_collection

PHOTO_URL = ["https://files.catbox.moe/20xca5.jpg"]  

@Client.on_message(filters.command("rank"))
async def rank(client, message):
    cursor = user_collection.find({}, {"_id": 0, "id": 1, "first_name": 1, "characters": 1})
    leaderboard_data = await cursor.to_list(length=None)
    leaderboard_data.sort(key=lambda x: len(x.get('characters', [])), reverse=True)
    leaderboard_data = leaderboard_data[:10]

    leaderboard_message = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
    for i, user in enumerate(leaderboard_data, start=1):
        user_id = user.get('id', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
        character_count = len(user.get('characters', []))
        leaderboard_message += f'{i}. <a href="tg://user?id={user_id}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'

    buttons = [
        [
            InlineKeyboardButton("✅ Top", callback_data="top"),
            InlineKeyboardButton("Top Group", callback_data="top_group"),
        ],
        [
            InlineKeyboardButton("MTOP", callback_data="mtop"),
            InlineKeyboardButton("Tokens", callback_data="tokens"),
        ],
    ]

    await message.reply_photo(
        photo=random.choice(PHOTO_URL),
        caption=leaderboard_message,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def update_caption(callback_query, caption, active_button):
    buttons = [
        [
            InlineKeyboardButton("✅ Top" if active_button == "top" else "Top", callback_data="top"),
            InlineKeyboardButton("✅ Top Group" if active_button == "top_group" else "Top Group", callback_data="top_group"),
        ],
        [
            InlineKeyboardButton("✅ MTOP" if active_button == "mtop" else "MTOP", callback_data="mtop"),
            InlineKeyboardButton("✅ Tokens" if active_button == "tokens" else "Tokens", callback_data="tokens"),
        ],
    ]

    await callback_query.edit_message_caption(
        caption=caption,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex("^top$"))
async def top_callback(client, callback_query):
    await asyncio.sleep(1)
    cursor = user_collection.find({}, {"_id": 0, "id": 1, "first_name": 1, "characters": 1})
    leaderboard_data = await cursor.to_list(length=None)
    leaderboard_data.sort(key=lambda x: len(x.get('characters', [])), reverse=True)
    leaderboard_data = leaderboard_data[:10]

    caption = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"
    for i, user in enumerate(leaderboard_data, start=1):
        user_id = user.get('id', 'Unknown')
        first_name = html.escape(user.get('first_name', 'Unknown'))[:15] + '...'
        character_count = len(user.get('characters', []))
        caption += f'{i}. <a href="tg://user?id={user_id}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'

    await update_caption(callback_query, caption, "top")

@Client.on_callback_query(filters.regex("^top_group$"))
async def top_group_callback(client, callback_query):
    await asyncio.sleep(1)
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ])
    leaderboard_data = await cursor.to_list(length=10)
    
    caption = "<b>TOP 10 GROUPS WHO GUESSED MOST CHARACTERS</b>\n\n"
    for i, group in enumerate(leaderboard_data, start=1):
        group_name = html.escape(group.get('group_name', 'Unknown'))[:15] + '...'
        count = group['count']
        caption += f'{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n'

    await update_caption(callback_query, caption, "top_group")

@Client.on_callback_query(filters.regex("^mtop$"))
async def mtop_callback(client, callback_query):
    await asyncio.sleep(1)
    top_users = await user_collection.find().sort("balance", -1).limit(10).to_list(length=10)

    caption = "<b>MTOP LEADERBOARD</b>\n\n🏆 Tᴏᴘ 10 Uꜱᴇʀs ʙʏ Cᴏɪɴs:\n\n"
    for rank, user in enumerate(top_users, start=1):
        user_id = user.get("id", "Unknown")
        first_name = user.get("first_name", "Unknown")
        coins = user.get("balance", 0)
        caption += f"{rank}. <a href='tg://user?id={user_id}'><b>{first_name}</b></a>: 💸 {coins} Coins\n"

    await update_caption(callback_query, caption, "mtop")

@Client.on_callback_query(filters.regex("^tokens$"))
async def tokens_callback(client, callback_query):
    await asyncio.sleep(1)
    top_users = await user_collection.find().sort("tokens", -1).limit(10).to_list(length=10)

    caption = "<b>Tokens LEADERBOARD</b>\n\n🏆 Tᴏᴘ 10 Uꜱᴇʀs ʙʏ Tokens:\n\n"
    for rank, user in enumerate(top_users, start=1):
        user_id = user.get("id", "Unknown")
        first_name = user.get("first_name", "Unknown")
        tokens = user.get("tokens", 0)
        caption += f"{rank}. <a href='tg://user?id={user_id}'><b>{first_name}</b></a>: 🪙 {tokens} Tokens\n"

    await update_caption(callback_query, caption, "tokens")