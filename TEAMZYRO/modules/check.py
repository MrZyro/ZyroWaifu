# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

# TEAMZYRO/commands/check.py
from TEAMZYRO import app, collection as character_collection, user_collection
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import asyncio 

@app.on_message(filters.command("check"))
async def check_character(client, message):
    args = message.command
    if len(args) < 2:
        await message.reply_text("Please provide a Character ID: `/check <character_id>`")
        return

    character_id = args[1]
    character = await character_collection.find_one({'id': character_id})

    if not character:
        await message.reply_text("Character not found.")
        return

    # Power nikaalo using rarity

    # Create the 'Who Have It' button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Who Have It", callback_data=f"whohaveit_{character_id}")]
    ])

    # Send character details
    text = (
        f"🌟 **Character Info**\n"
        f"🆔 ID: `{character_id}`\n"
        f"📛 Name: {character['name']}\n"
        f"📺 Anime: {character['anime']}\n"
        f"💎 Rarity: {character['rarity']}\n"
    )

    if 'vid_url' in character:
        await message.reply_video(character['vid_url'], caption=text, reply_markup=keyboard)
    else:
        await message.reply_photo(character['img_url'], caption=text, reply_markup=keyboard)


@app.on_callback_query(filters.regex("^whohaveit_"))
async def who_have_it(client, callback_query):
    character_id = callback_query.data.split("_")[1]

    # Find users who own the character
    users = await user_collection.find({'characters.id': character_id}).to_list(length=10)

    if not users:
        await callback_query.answer("No one owns this character yet!", show_alert=True)
        return

    # Generate top 10 owners list with count
    owner_text = "**🏆 Top 10 Users Who Own This Character:**\n\n"
    for i, user in enumerate(users, 1):
        user_name = user.get('first_name', 'Unknown')  # Use 'Unknown' if missing
        count = sum(1 for char in user.get("characters", []) if char["id"] == character_id)
        owner_text += f"{i}. [{user_name}](tg://user?id={user['id']}) — x{count}\n"

    # Edit message to include the owner list and remove the button
    await callback_query.message.edit_caption(
        caption=f"{callback_query.message.caption}\n\n{owner_text}",
        reply_markup=None
    )

