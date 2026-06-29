# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pymongo import MongoClient
from TEAMZYRO import *
from functools import wraps
x = 00000
sudo_users = db['sudo_users']

# Predefined powers
ALL_POWERS = [
    "add",  # Adds a new character
    "del",  # Deletes a character
    "up",   # Updates an existing character
    "app",  # Approves a request
    "inv",  # Approves an inventory request
    "VIP"
]

def require_power(required_power):
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message, *args, **kwargs):
            # Check if the message is a callback query or a regular message
            if isinstance(message, CallbackQuery):
                # This is a callback query, not a regular message
                user_id = message.from_user.id
                # If the user is the owner or a specific user ID, bypass the power check
                if user_id == OWNER_ID or user_id == x:
                    return await func(client, message, *args, **kwargs)

                # Otherwise, check if the user has the required power
                user_data = await sudo_users.find_one({"_id": user_id})
                if not user_data or not user_data.get("powers", {}).get(required_power, False):
                    # Use callback_query.answer for callback queries
                    await message.answer(f"You do not have the `{required_power}` power required to use this button.", show_alert=True)
                    return
                return await func(client, message, *args, **kwargs)

            # Regular message handling
            user_id = message.from_user.id
            # If the user is the owner or a specific user ID, bypass the power check
            if user_id == OWNER_ID or user_id == x:
                return await func(client, message, *args, **kwargs)

            # Otherwise, check if the user has the required power
            user_data = await sudo_users.find_one({"_id": user_id})
            if not user_data or not user_data.get("powers", {}).get(required_power, False):
                # Use message.reply_text for regular messages
                await message.reply_text(f"You do not have the `{required_power}` power required to use this command.")
                return
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator

async def is_vip_or_owner(user_id: int) -> bool:
    if user_id == OWNER_ID or user_id == x:
        return True
    user_data = await sudo_users.find_one({"_id": user_id})
    if user_data and user_data.get("powers", {}).get("VIP", False):
        return True
    return False
