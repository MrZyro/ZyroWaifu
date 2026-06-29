# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import random
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bson import ObjectId
from pyrogram import filters
from pyrogram.enums import ParseMode
from TEAMZYRO import *

user_shop_state = {}
DEFAULT_DISCOUNT = 12

RARITY_PRICE = {
    "⚪️ Common": 1000,
    "🟣 Rare": 5000,
    "🟡 Legendary": 15000,
    "🟢 Medium": 30000,
    "💮 Special Edition": 25000,
    "🔮 Limited Edition": 40000,
    "💸 Premium Edition": 30000,
}


# Safe split
def safe_split(data, sep="_", expected=2):
    parts = data.split(sep)
    if len(parts) < expected:
        parts += [None] * (expected - len(parts))
    return parts[:expected]


async def get_active_discount():
    discount = await discounts_collection.find_one({})
    if discount and discount["expires_at"] > datetime.utcnow():
        return discount["percent"]
    return DEFAULT_DISCOUNT


# ---------------- DISCOUNT SYSTEM ---------------- #

@app.on_message(filters.command("discount"))
async def set_discount(client, message):
    if message.from_user.id != OWNER_ID:
        return await message.reply("🚫 Only owners can set discounts.")

    args = message.text.split()

    if len(args) < 3:
        return await message.reply(
            "Usage:\n/discount <percent> <duration>\n\n"
            "Example:\n"
            "/discount 30 1d\n"
            "/discount 25 12h"
        )

    try:
        percent = int(args[1])
    except ValueError:
        return await message.reply("❌ Invalid percent value!")

    duration = args[2].lower()

    if duration.endswith("h"):
        hours = int(duration[:-1])
        expires = datetime.utcnow() + timedelta(hours=hours)

    elif duration.endswith("d"):
        days = int(duration[:-1])
        expires = datetime.utcnow() + timedelta(days=days)

    else:
        return await message.reply("❌ Duration must end with 'h' or 'd'.")

    await discounts_collection.delete_many({})
    await discounts_collection.insert_one({
        "percent": percent,
        "expires_at": expires
    })

    await message.reply(
        f"✅ Discount of {percent}% set for {duration} successfully!"
    )
    

def is_video(url):
    return any(url.lower().endswith(ext) for ext in [".mp4", ".mov", ".webm"])


# ---------------- SHOP MENU ---------------- #

@app.on_message(filters.command(["shop", "hshop", "hshopmenu"]))
async def shop_menu(client, message):
    keyboard = []
    for i, r in enumerate(RARITY_PRICE.keys()):
        keyboard.append(
            [InlineKeyboardButton(r, callback_data=f"xeno_{i}")]
        )

    await message.reply_photo(
        photo="https://files.catbox.moe/ohi1vs.jpg",
        caption="🌟 **Choose a rarity to browse the Bazaar!**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------- SHOW RARITY ---------------- #

@app.on_callback_query(filters.regex(r"^xeno_\d+$"))
async def show_rarity_list(client, callback_query):
    _, index_str = safe_split(callback_query.data, "_", 2)

    rarity_list = list(RARITY_PRICE.keys())
    rarity = rarity_list[int(index_str)]

    user_id = callback_query.from_user.id

    characters = await collection.find({"rarity": rarity}).to_list(None)
    if not characters:
        return await callback_query.answer("No characters found!", show_alert=True)

    random.shuffle(characters)

    user_shop_state[user_id] = {
        "rarity": rarity,
        "index": 0,
        "characters": characters[:5]
    }

    await show_character(client, callback_query.message, user_id)
    await callback_query.answer()


# ---------------- SHOW CHARACTER ---------------- #

async def show_character(client, msg, user_id):
    data = user_shop_state[user_id]
    char = data["characters"][data["index"]]

    price = RARITY_PRICE.get(char["rarity"], 1000)
    discount = await get_active_discount()
    discounted_price = int(price * (100 - discount) / 100)

    caption = (
        f"💎 <b>{char['name']}</b>\n"
        f"🏯 <b>Anime:</b> {char['anime']}\n"
        f"⭐ <b>Rarity:</b> {char['rarity']}\n"
        f"💰 <b>Price:</b> {discounted_price} Star Coins ({discount}% off!)\n"
        f"🆔 ID: <code>{char['id']}</code>"
    )

    keyboard = [
        [
            InlineKeyboardButton("⬅️ Prev", callback_data="prev_char"),
            InlineKeyboardButton("🪄 Claim", callback_data=f"claim_{data['index']}"),
            InlineKeyboardButton("➡️ Next", callback_data="next_char"),
        ],
        [InlineKeyboardButton("🔄 Refresh (5000💫)", callback_data="refresh_chars")]
    ]

    await msg.delete()

    if is_video(char["img_url"]):
        await msg.reply_video(
            video=char["img_url"],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    else:
        await msg.reply_photo(
            photo=char["img_url"],
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )


# ---------------- NAVIGATION ---------------- #

@app.on_callback_query(filters.regex("^next_char$"))
async def next_character(client, callback_query):
    user_id = callback_query.from_user.id
    state = user_shop_state.get(user_id)

    if not state:
        return await callback_query.answer("Start from /shop again!", True)

    if state["index"] >= len(state["characters"]) - 1:
        return await callback_query.answer("No more heroes!", True)

    state["index"] += 1
    await show_character(client, callback_query.message, user_id)
    await callback_query.answer()


@app.on_callback_query(filters.regex("^prev_char$"))
async def prev_character(client, callback_query):
    user_id = callback_query.from_user.id
    state = user_shop_state.get(user_id)

    if not state:
        return await callback_query.answer("Start from /shop again!", True)

    if state["index"] <= 0:
        return await callback_query.answer("Already at first hero!", True)

    state["index"] -= 1
    await show_character(client, callback_query.message, user_id)
    await callback_query.answer()


# ---------------- CLAIM ---------------- #

@app.on_callback_query(filters.regex(r"^claim_\d+$"))
async def claim_character(client, callback_query):
    _, index_str = safe_split(callback_query.data, "_", 2)

    user_id = callback_query.from_user.id
    state = user_shop_state.get(user_id)

    if not state:
        return await callback_query.answer("Open shop again!", True)

    char = state["characters"][int(index_str)]
    user = await user_collection.find_one({"id": user_id})

    if not user:
        return await callback_query.answer("Register first!", True)

    price = RARITY_PRICE.get(char["rarity"], 1000)
    discount = await get_active_discount()
    discounted_price = int(price * (100 - discount) / 100)

    if user.get("balance", 0) < discounted_price:
        return await callback_query.answer("Not enough Star Coins!", True)

    await user_collection.update_one(
        {"id": user_id},
        {
            "$inc": {"balance": -discounted_price},
            "$push": {"characters": {
                "_id": ObjectId(),
                "img_url": char["img_url"],
                "name": char["name"],
                "anime": char["anime"],
                "rarity": char["rarity"],
                "id": char["id"]
            }}
        }
    )

    await callback_query.answer(f"🎉 You claimed {char['name']}!", True)
