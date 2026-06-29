# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

# TEAMZYRO/commands/search_characters.py
from TEAMZYRO import app, collection, rarity_map2 as rarity_map
from pyrogram import Client, filters, enums
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def handle_search(client, message, query=None, page=1, is_callback=False):
    try:
        if not query:
            args = message.command
            if len(args) < 2:
                await message.reply_text("Please provide a character name. Usage: /sips {character name}")
                return
            query = " ".join(args[1:]).strip()

        per_page = 10
        skip = (page - 1) * per_page

        # Count the total characters
        total_characters = await collection.count_documents({"name": {"$regex": query, "$options": "i"}})

        if total_characters == 0:
            await message.reply_text(f"No characters found matching: {query}")
            return

        # Fetch the characters for the current page
        characters = await collection.find({"name": {"$regex": query, "$options": "i"}}).skip(skip).limit(per_page).to_list(length=per_page)

        # Create response message
        response = f"**Total Characters Found:** {total_characters}\n\n"
        for index, character in enumerate(characters, start=1 + skip):
            rarity_emoji = rarity_map.get(character['rarity'], "❓")  # Default to ❓ if rarity is not found
            response += (
                f"◈⌠{rarity_emoji}⌡ **{index}** {character['name']}\n"
                f"Anime: {character['anime']}\n"
                f"ID: {character['id']}\n\n"
            )

        # Create pagination buttons
        buttons = []
        if page > 1:
            buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"sips:{query}:{page - 1}"))
        if skip + per_page < total_characters:
            buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"sips:{query}:{page + 1}"))

        # Edit the message if it's a callback query, otherwise send a new one
        if is_callback:
            await message.edit_text(
                response,
                reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.reply_text(
                response,
                reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None,
                parse_mode=ParseMode.MARKDOWN
            )

    except Exception as e:
        error_message = f"Error: {str(e)}"
        if is_callback:
            await message.edit_text(error_message)
        else:
            await message.reply_text(error_message)

@app.on_message(filters.command("sips"))
async def search_characters(client, message):
    await handle_search(client, message)

@app.on_callback_query(filters.regex(r"^sips:(.+):(\d+)$"))
async def handle_pagination(client, callback_query):
    try:
        data = callback_query.data.split(":")
        query = data[1]
        page = int(data[2])

        # Edit the current message with new results
        await handle_search(client, callback_query.message, query=query, page=page, is_callback=True)

    except Exception as e:
        await callback_query.answer(f"Error: {str(e)}", show_alert=True)

