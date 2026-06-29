# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pymongo import MongoClient

from TEAMZYRO import OWNER_ID

from TEAMZYRO import app, db, require_power
from functools import wraps

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

# Command: /addsudo
@app.on_message(filters.command("saddsudo") & filters.reply)
@require_power("VIP")
async def add_sudo(client, message):
    
    replied_user_id = message.reply_to_message.from_user.id

    # Check if the user is already a sudo
    existing_user = await sudo_users.find_one({"_id": replied_user_id})
    if existing_user:
        await message.reply_text(f"User `{replied_user_id}` is already a sudo.")
        return

    # Add the user as a sudo
    sudo_users.update_one(
        {"_id": replied_user_id},
        {"$set": {"powers": {"add": True}}},  # Only giving the 'add' power
        upsert=True
    )
    await message.reply_text(f"User `{replied_user_id}` has been added as a sudo with 'add' power.")

@app.on_message(filters.command("sremovesudo"))
@require_power("VIP")
async def remove_sudo(client, message):
    # Get user ID from reply or command argument
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1 and message.command[1].isdigit():
        user_id = int(message.command[1])
    else:
        await message.reply_text("❌ Please reply to a user or provide a valid user ID.")
        return

    # Check if the user is a sudo
    existing_user = await sudo_users.find_one({"_id": user_id})
    if not existing_user:
        await message.reply_text(f"⚠️ User `{user_id}` is not a sudo.")
        return

    # Remove the user from sudo
    await sudo_users.delete_one({"_id": user_id})
    await message.reply_text(f"✅ User [{user_id}](tg://user?id={user_id}) has been removed from sudo.", disable_web_page_preview=True)


# Command: /editsudo
@app.on_message(filters.command("seditsudo") & filters.reply)
@require_power("VIP")
async def edit_sudo(client, message):
    
    replied_user_id = message.reply_to_message.from_user.id
    user_data = await sudo_users.find_one({"_id": replied_user_id})

    if not user_data:
        await message.reply_text("This user is not a sudo.")
        return

    # Generate inline keyboard with "Closed" button
    buttons = []
    powers = user_data.get("powers", {})
    for i, power in enumerate(ALL_POWERS):
        current_status = "Yes" if powers.get(power, False) else "No"
        buttons.append([
            InlineKeyboardButton(f"{power}", callback_data=f"noop"),
            InlineKeyboardButton(f"{current_status}", callback_data=f"toggle_{replied_user_id}_{power}")
        ])
    
    # Add the "Closed" button to close the keyboard
    buttons.append([InlineKeyboardButton("Closed", callback_data="close_keyboard")])

    keyboard = InlineKeyboardMarkup(buttons)

    await message.reply_text(f"Edit powers for `{replied_user_id}`:", reply_markup=keyboard)

# Callback handler for toggling powers
@app.on_callback_query(filters.regex(r"^toggle_(\d+)_(\w+)$"))
@require_power("VIP")
async def toggle_power(client, callback_query):

    user_id = int(callback_query.matches[0].group(1))
    power = callback_query.matches[0].group(2)

    user_data = await sudo_users.find_one({"_id": user_id})
    if not user_data:
        await callback_query.answer("User not found.", show_alert=True)
        return

    # Toggle the power
    current_status = user_data.get("powers", {}).get(power, False)
    new_status = not current_status
    await sudo_users.update_one(
        {"_id": user_id},
        {"$set": {f"powers.{power}": new_status}}
    )

    # Notify the user and update the keyboard
    await callback_query.answer(f"Power '{power}' updated to {'Yes' if new_status else 'No'}.", show_alert=True)

    user_data = await sudo_users.find_one({"_id": user_id})  # Fetch updated user data
    powers = user_data.get("powers", {})
    buttons = []
    for p in ALL_POWERS:
        status = "Yes" if powers.get(p, False) else "No"
        buttons.append([
            InlineKeyboardButton(f"{p}", callback_data=f"noop"),
            InlineKeyboardButton(f"{status}", callback_data=f"toggle_{user_id}_{p}")
        ])
    
    # Add the "Closed" button again after toggling
    buttons.append([InlineKeyboardButton("Closed", callback_data="close_keyboard")])

    keyboard = InlineKeyboardMarkup(buttons)
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

# Callback handler for closing the keyboard
@app.on_callback_query(filters.regex(r"^close_keyboard$"))
@require_power("VIP")
async def close_keyboard(client, callback_query):
    await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.answer("Keyboard closed.", show_alert=True)

# require_power decorator imported from TEAMZYRO package


# Command: /sudolist
@app.on_message(filters.command("sudolist"))
async def sudo_list(client, message):
    if message.from_user.id != OWNER_ID:
        await message.reply_text("You do not have permission to use this command.")
        return

    # Fetch all sudo users from the database
    users = await sudo_users.find().to_list(length=None)

    if not users:
        await message.reply_text("There are no sudo users.")
        return

    sudo_list_text = "🛠 **Sudo Users List:**\n\n"
    for user in users:
        user_id = user.get("_id")
        
        # Fetch user details from Telegram
        try:
            user_info = await client.get_users(user_id)
            first_name = user_info.first_name
        except:
            first_name = "Unknown"

        # Show user first name and mention link
        sudo_list_text += f"➤ [{first_name}](tg://user?id={user_id}) (`{user_id}`)\n"

    await message.reply_text(sudo_list_text, disable_web_page_preview=True)
            
