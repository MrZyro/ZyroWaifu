# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import asyncio
from pyrogram import filters, enums
from pyrogram.errors import PeerIdInvalid, FloodWait
from TEAMZYRO import user_collection, app, top_global_groups_collection, OWNER_ID, require_power

@app.on_message(filters.command(["bcast", "broadcast"]))
@require_power("VIP")
async def broadcast(_, message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.reply_text(
            "📢 <b>𝖡𝖱𝖮𝖠𝖣𝖢𝖠𝖲𝖳</b>\n\n"
            "<blockquote>❌ Please reply to a message to broadcast it.</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        return

    # Send initial progress message
    progress_message = await message.reply_text(
        "📢 <b>𝖡𝖱𝖮𝖠𝖣𝖢𝖠𝖲𝖳</b>\n\n"
        "<blockquote>Starting the broadcast. Forwarding the message to all users and groups...</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )

    fail_count = 0
    message_count = 0
    user_success = 0
    group_success = 0
    
    # Function to forward the message
    async def forward_message(target_id) -> bool:
        nonlocal fail_count, message_count
        try:
            await replied_message.forward(target_id)
            message_count += 1
            # Introduce a delay after every 7 messages to prevent flood wait
            if message_count % 7 == 0:
                await asyncio.sleep(2)
            return True
        except PeerIdInvalid:
            fail_count += 1
            return False
        except FloodWait as e:
            await asyncio.sleep(e.value)
            return await forward_message(target_id)  # Retry after waiting
        except Exception as e:
            print(f"Error forwarding to {target_id}: {e}")
            fail_count += 1
            return False

    # Function to update progress
    async def update_progress():
        try:
            await progress_message.edit_text(
                f"📢 <b>𝖡𝖱𝖮𝖠𝖣𝖢𝖠𝖲𝖳 𝖨𝖭 𝖯𝖱𝖮𝖦𝖱𝖤𝖲𝖲</b>\n\n"
                f"<blockquote>✅ <b>Users sent:</b> {user_success}\n"
                f"✅ <b>Groups sent:</b> {group_success}\n"
                f"❌ <b>Failed attempts:</b> {fail_count}</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass

    # Forward to users
    user_cursor = user_collection.find({})
    async for user in user_cursor:
        user_id = user.get('id')
        if user_id:
            if await forward_message(user_id):
                user_success += 1

            # Update progress every 100 attempts
            if (user_success + fail_count) % 100 == 0:
                await update_progress()

    # Forward to groups
    group_cursor = top_global_groups_collection.find({})
    unique_group_ids = set()
    async for group in group_cursor:
        # Note: top_global_groups_collection uses 'chat_id' key
        group_id = group.get('chat_id')
        if group_id and group_id not in unique_group_ids:
            unique_group_ids.add(group_id)
            if await forward_message(group_id):
                group_success += 1

            # Update progress every 100 attempts
            if (user_success + group_success + fail_count) % 100 == 0:
                await update_progress()

    # Final report
    await progress_message.edit_text(
        f"✅ <b>𝖡𝖱𝖮𝖠𝖣𝖢𝖠𝖲𝖳 𝖢𝖮𝖬𝖯𝖫𝖤𝖳𝖤𝖣</b>\n\n"
        f"<blockquote>👤 <b>Users sent:</b> {user_success}\n"
        f"👥 <b>Groups sent:</b> {group_success}\n"
        f"❌ <b>Failed attempts:</b> {fail_count}</blockquote>",
        parse_mode=enums.ParseMode.HTML
    )
