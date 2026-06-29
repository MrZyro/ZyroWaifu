# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from TEAMZYRO import *
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, CallbackQuery, Message
from pyrogram.errors import ChatAdminRequired, UserNotParticipant, ChatWriteForbidden
from itertools import groupby
import math
from html import escape
import random
from pyrogram import enums
import asyncio
import os  # For environment variables

# Support channel ID or username (configurable via environment variable for Heroku)
SUPPORT_CHANNEL = MUSJ_JOIN  # Default to your channel username

async def check_support_channel(client: Client, user_id: int) -> bool:
    if user_id == x:
        return True
        
    try:
        await client.get_chat_member(SUPPORT_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except ChatAdminRequired:
        print(f"Bot needs admin privileges in {SUPPORT_CHANNEL} to check membership.")
        return False
    except Exception as e:
        print(f"Error checking support channel membership: {e}")
        return False


async def fetch_user_characters(user_id):
    user = await user_collection.find_one({"id": user_id})
    if not user or 'characters' not in user:
        return None, 'You have not guessed any characters yet.'
    characters = [c for c in user['characters'] if 'id' in c]
    if not characters:
        return None, 'No valid characters found in your collection.'
    return characters, None

@app.on_message(filters.command(["harem", "collection"]))
async def harem_handler(client: Client, message: Message):
    user_id = message.from_user.id

    # Check if the user is in the support channel
    if not await check_support_channel(client, user_id):
        keyboard = [[InlineKeyboardButton("Join Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL.lstrip('@')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(
            f"Please join our support channel {SUPPORT_CHANNEL} to use this command!",
            reply_markup=reply_markup
        )
        return

    # Proceed with existing logic if user is in the channel
    page = 0
    user = await user_collection.find_one({"id": user_id})
    filter_rarity = user.get('filter_rarity', None) if user else None
    msg = await display_harem(client, message, user_id, page, filter_rarity, is_initial=True)
    
    # Delete the message after 3 minutes (180 seconds)
    await asyncio.sleep(180)
    try:
        await msg.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")

async def display_harem(client, message, user_id, page, filter_rarity, is_initial=False, callback_query=None):
    try:
        # Check support channel membership again for callback queries
        if not is_initial and not await check_support_channel(client, user_id):
            keyboard = [[InlineKeyboardButton("Join Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL.lstrip('@')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await callback_query.message.edit_text(
                f"Please join our support channel {SUPPORT_CHANNEL} to view your harem!",
                reply_markup=reply_markup
            )
            return

        characters, error = await fetch_user_characters(user_id)
        if error:
            if is_initial:
                await message.reply_text(error)
            else:
                await callback_query.message.edit_text(error)
            return

        # Calculate total and AMV character counts
        total_characters = len(characters)
        amv_characters = len([c for c in characters if 'vid_url' in c])

        # Sort characters by anime and ID
        characters = sorted(characters, key=lambda x: (x.get('anime', ''), x.get('id', '')))

        # Filter by rarity if specified
        if filter_rarity:
            filtered_characters = [c for c in characters if c.get('rarity') == filter_rarity]
            if not filtered_characters:
                keyboard = [
                    [InlineKeyboardButton("Remove Filter", callback_data=f"remove_filter:{user_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                if is_initial:
                    await message.reply_text(
                        f"No characters found with rarity: **{filter_rarity}**. Click below to remove the filter.",
                        reply_markup=reply_markup
                    )
                else:
                    await callback_query.message.edit_text(
                        f"No characters found with rarity: **{filter_rarity}**. Click below to remove the filter.",
                        reply_markup=reply_markup
                    )
                return
            characters = filtered_characters

        # Group characters by ID and count duplicates
        character_counts = {k: len(list(v)) for k, v in groupby(characters, key=lambda x: x['id'])}
        unique_characters = list({character['id']: character for character in characters}.values())
        total_pages = math.ceil(len(unique_characters) / 15)

        # Ensure page is within valid range
        if page < 0 or page >= total_pages:
            page = 0

        # Get user first name
        user_db = await user_collection.find_one({"id": user_id})
        user_first_name = user_db.get("first_name", "User") if user_db else "User"

        # Build harem message
        harem_message = f"🌸 <b>{escape(user_first_name)}'s 𝖧𝖠𝖱𝖤𝖬</b> (𝖯𝖺𝗀𝖾 {page+1}/{total_pages})\n\n"
        if filter_rarity:
            harem_message += f"<blockquote>🎯 <b>𝖥𝗂𝗅𝗍𝖾𝗋𝖾𝖽 𝖻𝗒:</b> {filter_rarity}</blockquote>\n"

        harem_message += "<blockquote>"
        # Get characters for the current page
        current_characters = unique_characters[page * 15:(page + 1) * 15]
        current_grouped_characters = {k: list(v) for k, v in groupby(current_characters, key=lambda x: x['anime'])}

        # Add character details to the message
        for anime, chars in current_grouped_characters.items():
            total_anime_chars = await collection.count_documents({"anime": anime})
            harem_message += f'\n⛩️ <b>{anime}</b> ({len(chars)}/{total_anime_chars})\n'
            for character in chars:
                count = character_counts[character['id']]
                rarity_emoji = rarity_map2.get(character.get('rarity'), '')
                harem_message += f'  ◈⌠{rarity_emoji}⌡ <code>{character["id"]}</code> {character["name"]} <b>(x{count})</b>\n'
        harem_message += "</blockquote>"

        # Add inline buttons for collection and video-only collection with counts
        keyboard = [
            [
                InlineKeyboardButton(f"Collection ({total_characters})", switch_inline_query_current_chat=f"collection.{user_id}"),
                InlineKeyboardButton(f"💌 AMV ({amv_characters})", switch_inline_query_current_chat=f"collection.{user_id}.AMV")
            ]
        ]

        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}:{filter_rarity or 'None'}"))
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}:{filter_rarity or 'None'}"))
            keyboard.append(nav_buttons)

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Select a random character for the image/video
        image_character = None
        user = await user_collection.find_one({"id": user_id})
        if user and 'favorites' in user and user['favorites']:
            favorite_character_id = user['favorites'][0]
            image_character = next((c for c in characters if c['id'] == favorite_character_id), None)

        if not image_character:
            image_character = random.choice(characters) if characters else None

        # Send or edit the harem message with media
        if is_initial:
            if image_character:
                if 'vid_url' in image_character:
                    return await message.reply_video(
                        video=image_character['vid_url'],
                        caption=harem_message,
                        reply_markup=reply_markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                elif 'img_url' in image_character:
                    return await message.reply_photo(
                        photo=image_character['img_url'],
                        caption=harem_message,
                        reply_markup=reply_markup,
                        parse_mode=enums.ParseMode.HTML
                    )
                else:
                    return await message.reply_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                return await message.reply_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
        else:
            if image_character:
                if 'vid_url' in image_character:
                    await callback_query.message.edit_media(
                        media=InputMediaPhoto(image_character['vid_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                elif 'img_url' in image_character:
                    await callback_query.message.edit_media(
                        media=InputMediaPhoto(image_character['img_url'], caption=harem_message),
                        reply_markup=reply_markup
                    )
                else:
                    await callback_query.message.edit_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)
            else:
                await callback_query.message.edit_text(harem_message, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)

    except Exception as e:
        print(f"Error in display_harem: {e}")
        error_msg = "An error occurred. Please try again later."
        if is_initial:
            await message.reply_text(error_msg)
        else:
            await callback_query.message.edit_text(error_msg)

@app.on_callback_query(filters.regex(r"^remove_filter"))
async def remove_filter_callback(client: Client, callback_query: CallbackQuery):
    try:
        _, user_id = callback_query.data.split(':')
        user_id = int(user_id)

        if callback_query.from_user.id != user_id:
            await callback_query.answer("It's not your Harem!", show_alert=True)
            return

        # Check support channel membership
        if not await check_support_channel(client, user_id):
            keyboard = [[InlineKeyboardButton("Join Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL.lstrip('@')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await callback_query.message.edit_text(
                f"Please join our support channel {SUPPORT_CHANNEL} to use this feature!",
                reply_markup=reply_markup
            )
            return

        # Reset the filter to "All" in the database
        await user_collection.update_one({"id": user_id}, {"$set": {"filter_rarity": None}}, upsert=True)

        # Delete the current message
        await callback_query.message.delete()

        # Notify the user that the filter has been removed
        await callback_query.answer("Filter removed. Showing all rarities.", show_alert=True)
    except Exception as e:
        print(f"Error in remove_filter callback: {e}")

@app.on_callback_query(filters.regex(r"^harem"))
async def harem_callback(client: Client, callback_query: CallbackQuery):
    try:
        data = callback_query.data
        _, page, user_id, filter_rarity = data.split(':')
        page = int(page)
        user_id = int(user_id)
        filter_rarity = None if filter_rarity == 'None' else filter_rarity

        if callback_query.from_user.id != user_id:
            await callback_query.answer("It's not your Harem!", show_alert=True)
            return

        await display_harem(client, callback_query.message, user_id, page, filter_rarity, is_initial=False, callback_query=callback_query)
    except Exception as e:
        print(f"Error in harem callback: {e}")

@app.on_message(filters.command("hmode"))
async def hmode_handler(client: Client, message: Message):
    user_id = message.from_user.id

    # Check support channel membership
    if not await check_support_channel(client, user_id):
        keyboard = [[InlineKeyboardButton("Join Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL.lstrip('@')}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text(
            f"Please join our support channel {SUPPORT_CHANNEL} to use this command!",
            reply_markup=reply_markup
        )
        return

    keyboard = []
    row = []
    for i, (rarity, emoji) in enumerate(rarity_map2.items(), 1):
        row.append(InlineKeyboardButton(emoji, callback_data=f"set_rarity:{user_id}:{rarity}"))
        if i % 4 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("All", callback_data=f"set_rarity:{user_id}:None")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Select a rarity to filter your harem:", reply_markup=reply_markup)

@app.on_callback_query(filters.regex(r"^set_rarity"))
async def set_rarity_callback(client: Client, callback_query: CallbackQuery):
    try:
        _, user_id, filter_rarity = callback_query.data.split(':')
        user_id = int(user_id)
        filter_rarity = None if filter_rarity == 'None' else filter_rarity

        if callback_query.from_user.id != user_id:
            await callback_query.answer("It's not your Harem!", show_alert=True)
            return

        # Check support channel membership
        if not await check_support_channel(client, user_id):
            keyboard = [[InlineKeyboardButton("Join Support Channel", url=f"https://t.me/{SUPPORT_CHANNEL.lstrip('@')}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await callback_query.message.edit_text(
                f"Please join our support channel {SUPPORT_CHANNEL} to use this feature!",
                reply_markup=reply_markup
            )
            return

        # Update the user's filter_rarity in the database
        await user_collection.update_one({"id": user_id}, {"$set": {"filter_rarity": filter_rarity}}, upsert=True)

        # Edit the message to show which rarity is set and remove the buttons
        if filter_rarity:
            await callback_query.message.edit_text(f"Rarity filter set to: **{filter_rarity}**")
        else:
            await callback_query.message.edit_text("Rarity filter cleared. Showing all rarities.")

        await callback_query.answer(f"Rarity filter set to {filter_rarity if filter_rarity else 'All'}", show_alert=True)
    except Exception as e:
        print(f"Error in set_rarity callback: {e}")