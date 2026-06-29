# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

from TEAMZYRO import user_collection, ZYRO

# Dictionary to store pending gifts
pending_gifts = {}

# Function to auto-cancel gift after 1 hour
async def auto_cancel_gift(sender_id, receiver_id):
    await asyncio.sleep(3600)  # Wait for 1 hour (3600 seconds)

    # Check if the gift is still pending and not processed
    if (sender_id, receiver_id) in pending_gifts and not pending_gifts[(sender_id, receiver_id)]['processed']:
        del pending_gifts[(sender_id, receiver_id)]
        print(f"Gift from {sender_id} to {receiver_id} auto-cancelled after 1 hour.")  # Debugging

@ZYRO.on_message(filters.command("gift"))
async def gift(client, message):
    sender_id = message.from_user.id

    # Check if the user already has a pending gift
    for _sender_id, _ in pending_gifts.keys():
        if _sender_id == sender_id:
            await message.reply_text(
                "You already have a gift processing. Please confirm or cancel it before sending another gift.",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    if not message.reply_to_message:
        await message.reply_text(
            "You need to reply to a user's message to gift a character!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_username = message.reply_to_message.from_user.username
    receiver_first_name = message.reply_to_message.from_user.first_name

    if sender_id == receiver_id:
        await message.reply_text(
            "You can't gift a character to yourself!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if len(message.command) != 2:
        await message.reply_text(
            "You need to provide a character ID!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    character_id = message.command[1]

    sender = await user_collection.find_one({'id': sender_id})

    # Check if the sender has the character
    character = next((char for char in sender['characters'] if char['id'] == character_id), None)

    if not character:
        await message.reply_text(
            "You don't have this character in your collection!",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Add gift to pending gifts with a processed flag
    pending_gifts[(sender_id, receiver_id)] = {
        'character': character,
        'receiver_username': receiver_username,
        'receiver_first_name': receiver_first_name,
        'processed': False  # Initialize processed flag
    }

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Confirm Gift", callback_data="confirm_gift")],
            [InlineKeyboardButton("❌ Cancel Gift", callback_data="cancel_gift")]
        ]
    )

    # Prepare character details for caption
    caption = (
        f"🎁 <b>Gift Character</b>\n"
        f"🌸 <b>{character.get('name', 'Unknown')}</b>\n"
    )

    # Send the character image with caption and buttons
    if character.get('img_url'):
        await message.reply_photo(
            photo=character['img_url'],
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    else:
        # fallback if no image
        await message.reply_text(
            caption,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

    # Start the auto-cancel task for this gift
    asyncio.create_task(auto_cancel_gift(sender_id, receiver_id))


@ZYRO.on_callback_query(filters.create(lambda _, __, query: query.data in ["confirm_gift", "cancel_gift"]))
async def on_callback_query(client, callback_query):
    sender_id = callback_query.from_user.id

    # Check if there's a pending gift for the sender
    for (_sender_id, receiver_id), gift in pending_gifts.items():
        if _sender_id == sender_id:
            break
    else:
        await callback_query.answer("This is not for you!", show_alert=True)
        return

    if callback_query.data == "confirm_gift":
        # Check if the gift has already been processed
        if gift['processed']:
            await callback_query.answer("This gift has already been processed.", show_alert=True)
            return

        # Mark the gift as processed
        gift['processed'] = True

        sender = await user_collection.find_one({'id': sender_id})
        receiver = await user_collection.find_one({'id': receiver_id})

        # Transfer the character
        sender['characters'].remove(gift['character'])
        await user_collection.update_one({'id': sender_id}, {'$set': {'characters': sender['characters']}})

        if receiver:
            await user_collection.update_one({'id': receiver_id}, {'$push': {'characters': gift['character']}})
        else:
            await user_collection.insert_one({
                'id': receiver_id,
                'username': gift['receiver_username'],
                'first_name': gift['receiver_first_name'],
                'characters': [gift['character']],
            })

        del pending_gifts[(sender_id, receiver_id)]

        # Edit the message to disable the buttons and update caption
        new_caption = (
            f"🎉 <b>Gift Successful!</b>\n\n"
            f"You have successfully gifted your character to "
            f"<a href='tg://user?id={receiver_id}'>{gift['receiver_first_name']}</a>!"
        )
        try:
            await callback_query.message.edit_caption(
                caption=new_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=None
            )
        except Exception:
            await callback_query.message.edit_text(
                new_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=None
            )

    elif callback_query.data == "cancel_gift":
        del pending_gifts[(sender_id, receiver_id)]
        cancel_caption = "❌️ Gift cancelled."
        try:
            await callback_query.message.edit_caption(
                caption=cancel_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=None
            )
        except Exception:
            await callback_query.message.edit_text(
                cancel_caption,
                parse_mode=ParseMode.HTML,
                reply_markup=None
            )
