# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import time
import secrets
import string
import asyncio
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from TEAMZYRO import app, user_collection, require_power, db, application

# Global variables for tracking active transfers
transfer_in_progress = False
active_transfer = None  # Dict storing metadata of the current active transfer
processing_locks = set()  # Set of active transfer_ids currently processing in db

TRANSFER_TIMEOUT = 60  # seconds
transfer_logs = db['transfer_logs']

# Create a TTL index so MongoDB automatically deletes logs older than 1 hour (3600 seconds)
async def create_ttl_index():
    try:
        await transfer_logs.create_index("createdAt", expireAfterSeconds=3600)
    except Exception:
        pass
# Hook index creation to post_init to execute safely in the event loop
original_post_init = getattr(application, 'post_init', None)

async def transfer_post_init(app_ptb):
    if original_post_init:
        await original_post_init(app_ptb)
    asyncio.create_task(create_ttl_index())

application.post_init = transfer_post_init


def is_transfer_active_and_valid():
    global active_transfer, transfer_in_progress
    if not transfer_in_progress or not active_transfer:
        return False
    if time.time() - active_transfer["timestamp"] > TRANSFER_TIMEOUT:
        # Expired, clear states
        transfer_in_progress = False
        active_transfer = None
        return False
    return True


def generate_transfer_id():
    return "TR_" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))


# Step 1: Transfer command triggers confirmation buttons
@app.on_message(filters.command("transfer"))
@require_power("VIP")
async def transfer_collection(client: Client, message: Message):
    global transfer_in_progress, active_transfer
    args = message.command[1:]
    if len(args) != 2:
        return await message.reply_text("Incorrect format. Use: `/transfer user_id owner_id`", quote=True)

    user_id = args[0]
    owner_id = args[1]

    # Validate numeric input
    if not user_id.isdigit() or not owner_id.isdigit():
        return await message.reply_text("Please provide valid numeric IDs.")

    if user_id == owner_id:
        return await message.reply_text("User ID and Owner ID must be different.")

    # Check global lock
    if is_transfer_active_and_valid():
        return await message.reply_text(
            f"⚠️ A transfer is already in progress (requested by user ID `{active_transfer['requester_id']}`). "
            "Please complete or cancel it first, or wait for it to expire.",
            quote=True
        )

    # Try finding user and owner with int or string IDs
    user = await user_collection.find_one({'id': {"$in": [int(user_id), str(user_id)]}})
    if not user:
        return await message.reply_text('User not found.')

    owner = await user_collection.find_one({'id': {"$in": [int(owner_id), str(owner_id)]}})
    if not owner:
        return await message.reply_text('Owner not found.')

    user_chars = user.get('characters', [])
    if not user_chars:
        return await message.reply_text(f"❌ User `{user_id}` has no characters to transfer.")

    from_id = message.from_user.id
    transfer_id = generate_transfer_id()

    # Lock transfer
    transfer_in_progress = True
    active_transfer = {
        "transfer_id": transfer_id,
        "user_id": user_id,
        "owner_id": owner_id,
        "requester_id": from_id,
        "timestamp": time.time()
    }

    text = (
        f"⚠️ **Confirm Character Transfer?**\n\n"
        f"👤 From: `{user_id}` (has {len(user_chars)} characters)\n"
        f"➡️ To: `{owner_id}`\n"
        f"🆔 Transfer ID: `{transfer_id}`\n\n"
        f"Click the appropriate button below to proceed or cancel. This prompt will expire in 60 seconds."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirm Transfer", callback_data=f"confirm_tr:{transfer_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_tr:{transfer_id}")
            ]
        ]
    )

    await message.reply_text(text, reply_markup=keyboard, quote=True)


# Step 2: Handle confirmation (ONE-WAY ONLY)
@app.on_callback_query(filters.regex(r"^confirm_tr:(\w+)$"))
async def confirm_transfer_callback(client: Client, callback_query: CallbackQuery):
    global transfer_in_progress, active_transfer
    transfer_id = callback_query.data.split(":")[1]

    # Pre-empt double clicks
    if transfer_id in processing_locks:
        return await callback_query.answer("⚠️ Transfer already in progress. Please wait...", show_alert=True)

    processing_locks.add(transfer_id)

    try:
        # Check if active transfer is valid and matching the transfer_id
        if not is_transfer_active_and_valid() or not active_transfer or active_transfer["transfer_id"] != transfer_id:
            await callback_query.edit_message_text("❌ This transfer request has expired or is invalid.")
            return

        requester_id = active_transfer["requester_id"]
        if callback_query.from_user.id != requester_id:
            await callback_query.answer("You're not authorized to confirm this transfer.", show_alert=True)
            return

        user_id = active_transfer["user_id"]
        owner_id = active_transfer["owner_id"]

        # Match IDs in DB whether stored as int or string
        user = await user_collection.find_one({'id': {"$in": [int(user_id), user_id]}})
        owner = await user_collection.find_one({'id': {"$in": [int(owner_id), owner_id]}})

        if not user or not owner:
            await callback_query.edit_message_text("❌ User or Owner not found.")
            transfer_in_progress = False
            active_transfer = None
            return

        user_chars = user.get('characters', [])
        if not user_chars:
            await callback_query.edit_message_text(f"❌ User `{user_id}` has no characters to transfer.")
            transfer_in_progress = False
            active_transfer = None
            return

        # Transfer characters from user -> owner
        await user_collection.update_one(
            {'id': {"$in": [int(owner_id), owner_id]}},
            {'$push': {'characters': {'$each': user_chars}}}
        )
        await user_collection.update_one(
            {'id': {"$in": [int(user_id), user_id]}},
            {'$set': {'characters': []}}
        )

        # Log transfer to MongoDB for 1-hour undo/back functionality
        transfer_doc = {
            "_id": transfer_id,
            "user_id": user_id,
            "owner_id": owner_id,
            "characters": user_chars,
            "timestamp": time.time(),
            "createdAt": datetime.utcnow(),  # MongoDB BSON Date for TTL index auto-deletion
            "status": "completed"
        }
        await transfer_logs.insert_one(transfer_doc)

        await callback_query.edit_message_text(
            f"✅ **Transfer Successful!**\n\n"
            f"👤 From: `{user_id}`\n"
            f"➡️ To: `{owner_id}`\n"
            f"📦 Characters Transferred: `{len(user_chars)}`\n\n"
            f"🆔 **Transfer ID:** `{transfer_id}`\n"
            f"🕒 *This transfer can be reverted within 1 hour using `/backtransfer {transfer_id}`*"
        )

        # Clear state
        transfer_in_progress = False
        active_transfer = None

    finally:
        processing_locks.discard(transfer_id)


# Step 3: Handle cancellation
@app.on_callback_query(filters.regex(r"^cancel_tr:(\w+)$"))
async def cancel_transfer_callback(client: Client, callback_query: CallbackQuery):
    global transfer_in_progress, active_transfer
    transfer_id = callback_query.data.split(":")[1]

    if not active_transfer or active_transfer["transfer_id"] != transfer_id:
        return await callback_query.answer("❌ This transfer is no longer active or has expired.", show_alert=True)

    requester_id = active_transfer["requester_id"]
    if callback_query.from_user.id != requester_id:
        return await callback_query.answer("You can't cancel this action.", show_alert=True)

    # Clear state
    transfer_in_progress = False
    active_transfer = None

    await callback_query.edit_message_text("🚫 Transfer cancelled by user.")


# Step 4: Revert (rollback/back) transfer command (1 hour validity)
@app.on_message(filters.command(["backtransfer", "untransfer", "trback"]))
@require_power("VIP")
async def back_transfer(client: Client, message: Message):
    args = message.command[1:]
    if len(args) != 1:
        return await message.reply_text("Incorrect format. Use: `/backtransfer <transfer_id>`", quote=True)

    transfer_id = args[0]
    log = await transfer_logs.find_one({"_id": transfer_id})
    if not log:
        return await message.reply_text(f"❌ Transfer ID `{transfer_id}` not found in database.", quote=True)

    if log.get("status") == "reverted":
        return await message.reply_text(f"❌ Transfer `{transfer_id}` has already been reverted.", quote=True)

    # Check 1 hour validity (3600 seconds)
    elapsed = time.time() - log["timestamp"]
    if elapsed > 3600:
        hours_elapsed = elapsed / 3600.0
        return await message.reply_text(
            f"❌ Transfer `{transfer_id}` was done {hours_elapsed:.1f} hours ago.\n"
            f"Rollback is only valid for up to 1 hour.",
            quote=True
        )

    user_id = log["user_id"]
    owner_id = log["owner_id"]
    transferred_chars = log["characters"]

    # Match owner and user documents
    owner_db = await user_collection.find_one({'id': {"$in": [int(owner_id), str(owner_id)]}})
    if not owner_db:
        return await message.reply_text(f"❌ Receiver owner `{owner_id}` document not found in DB. Cannot revert.", quote=True)

    def get_char_id(char):
        if isinstance(char, dict):
            return str(char.get("id"))
        return str(char)

    owner_chars = owner_db.get("characters", [])
    new_owner_chars = list(owner_chars)

    # Precise removal of exact transferred characters from receiver
    reverted_count = 0
    for t_char in transferred_chars:
        t_id = get_char_id(t_char)
        for idx, o_char in enumerate(new_owner_chars):
            if get_char_id(o_char) == t_id:
                new_owner_chars.pop(idx)
                reverted_count += 1
                break

    # Update owner (remove characters)
    await user_collection.update_one(
        {'id': {"$in": [int(owner_id), str(owner_id)]}},
        {'$set': {'characters': new_owner_chars}}
    )

    # Push characters back to original owner
    user_db = await user_collection.find_one({'id': {"$in": [int(user_id), str(user_id)]}})
    if user_db:
        await user_collection.update_one(
            {'id': {"$in": [int(user_id), str(user_id)]}},
            {'$push': {'characters': {'$each': transferred_chars}}}
        )
    else:
        # Recreate user document if it was deleted
        try:
            tg_user = await client.get_users(int(user_id))
            username = tg_user.username
            first_name = tg_user.first_name
        except Exception:
            username = None
            first_name = f"User {user_id}"

        await user_collection.insert_one({
            "id": int(user_id),
            "username": username,
            "first_name": first_name,
            "characters": transferred_chars
        })

    # Mark transfer as reverted in log database
    await transfer_logs.update_one(
        {"_id": transfer_id},
        {"$set": {"status": "reverted"}}
    )

    await message.reply_text(
        f"✅ **Transfer Reverted Successfully!**\n\n"
        f"🆔 **Transfer ID:** `{transfer_id}`\n"
        f"👤 Returned `{reverted_count}` characters back to original user `{user_id}`.\n"
        f"➡️ Removed from user `{owner_id}`.",
        quote=True
    )
