# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import asyncio
import uuid
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from TEAMZYRO import user_collection, ZYRO

# Dictionary to store pending trades
pending_trades = {}

# List to lock users with active trades
lock = []

# Function to auto-cancel trade after 10 minutes
async def auto_cancel_trade(trade_id, sender_id, receiver_id):
    await asyncio.sleep(600)  # Wait for 10 minutes (600 seconds)
    if trade_id in pending_trades and not pending_trades[trade_id]['processed']:
        del pending_trades[trade_id]
        if sender_id in lock:
            lock.remove(sender_id)
        if receiver_id in lock:
            lock.remove(receiver_id)
        print(f"Trade {trade_id} from {sender_id} to {receiver_id} auto-cancelled after 10 minutes.")

@ZYRO.on_message(filters.command("trade"))
async def trade(client, message):
    sender_id = message.from_user.id

    # Check if sender is locked (already in a trade)
    if sender_id in lock:
        await message.reply_text(
            "You already have a trade in progress. Please confirm or cancel it before starting a new trade.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if not message.reply_to_message:
        await message.reply_text(
            "You need to reply to a user's message to trade a character!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text(
            "You can't trade a character with yourself!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if receiver_id in lock:
        await message.reply_text(
            f"{message.reply_to_message.from_user.mention} is already in a trade. Please wait until their current trade is completed.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if len(message.command) != 3:
        await message.reply_text(
            "You need to provide your character ID and the other user's character ID! Usage: /trade <my_char_id> <user_char_id>",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    sender_char_id, receiver_char_id = message.command[1], message.command[2]

    # Fetch sender and receiver from database
    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    if not sender or not receiver:
        await message.reply_text(
            "One of the users is not found in the database!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check if sender has their character
    sender_char = next((char for char in sender['characters'] if char['id'] == sender_char_id), None)
    if not sender_char:
        await message.reply_text(
            f"You don't have the character with ID **{sender_char_id}** in your collection!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Check if receiver has their character
    receiver_char = next((char for char in receiver['characters'] if char['id'] == receiver_char_id), None)
    if not receiver_char:
        await message.reply_text(
            f"{message.reply_to_message.from_user.mention} doesn't have the character with ID **{receiver_char_id}** in their collection!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Generate unique trade ID
    trade_id = str(uuid.uuid4())

    # Add users to lock
    lock.append(sender_id)
    lock.append(receiver_id)

    # Store trade details
    pending_trades[trade_id] = {
        'sender_id': sender_id,
        'sender_char': sender_char,
        'receiver_id': receiver_id,
        'receiver_char': receiver_char,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name,
        'processed': False,
        'message_id': None  # Will be updated after sending the message
    }

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Confirm Trade", callback_data=f"confirm_trade_{trade_id}")],
            [InlineKeyboardButton("Cancel Trade", callback_data=f"cancel_trade_{trade_id}")]
        ]
    )

    # Send trade proposal message
    trade_message = await message.reply_text(
        f"{message.reply_to_message.from_user.mention}, do you agree to trade your character (ID: {receiver_char_id}) "
        f"with {message.from_user.mention}'s character (ID: {sender_char_id})?",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

    # Store message ID for potential updates
    pending_trades[trade_id]['message_id'] = trade_message.id

    # Start auto-cancel task
    asyncio.create_task(auto_cancel_trade(trade_id, sender_id, receiver_id))

@ZYRO.on_callback_query(filters.create(lambda _, __, query: query.data.startswith(("confirm_trade_", "cancel_trade_"))))
async def on_trade_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Extract trade ID from callback data
    trade_id = data.split("_", 2)[-1]
    trade = pending_trades.get(trade_id)

    if not trade:
        await callback_query.answer("This trade is no longer available.", show_alert=True)
        return

    # Check if trade is already processed (prevents multiple clicks)
    if trade['processed']:
        await callback_query.answer("This trade has already been processed.", show_alert=True)
        return

    if data.startswith("confirm_trade_"):
        if user_id != trade['receiver_id']:
            await callback_query.answer("Only the trade recipient can confirm this trade!", show_alert=True)
            return

        # Mark trade as processed to block further clicks
        trade['processed'] = True

        # Perform character swap
        sender = await user_collection.find_one({'id': trade['sender_id']})
        receiver = await user_collection.find_one({'id': trade['receiver_id']})

        sender['characters'].remove(trade['sender_char'])
        sender['characters'].append(trade['receiver_char'])
        receiver['characters'].remove(trade['receiver_char'])
        receiver['characters'].append(trade['sender_char'])

        await user_collection.update_one({'id': trade['sender_id']}, {'$set': {'characters': sender['characters']}})
        await user_collection.update_one({'id': trade['receiver_id']}, {'$set': {'characters': receiver['characters']}})

        # Unlock users
        if trade['sender_id'] in lock:
            lock.remove(trade['sender_id'])
        if trade['receiver_id'] in lock:
            lock.remove(trade['receiver_id'])

        # Remove trade
        del pending_trades[trade_id]

        # Update message
        await callback_query.message.edit_text(
            f"Trade successful! Characters have been swapped between [{trade['receiver_first_name']}](tg://user?id={trade['receiver_id']}) "
            f"and [{callback_query.from_user.first_name}](tg://user?id={trade['sender_id']}).",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=None
        )

    elif data.startswith("cancel_trade_"):
        if user_id not in [trade['sender_id'], trade['receiver_id']]:
            await callback_query.answer("This is not your trade!", show_alert=True)
            return

        # Mark trade as processed to block further clicks
        trade['processed'] = True

        # Unlock users
        if trade['sender_id'] in lock:
            lock.remove(trade['sender_id'])
        if trade['receiver_id'] in lock:
            lock.remove(trade['receiver_id'])

        # Remove trade
        del pending_trades[trade_id]

        # Update message
        await callback_query.message.edit_text(
            "❌️ Trade cancelled.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=None
        )
