# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters, enums
from pyrogram.types import Message
from TEAMZYRO import app, user_collection
import random
import asyncio

# Concurrency lock to prevent spam and race conditions
active_coinflips = set()

@app.on_message(filters.command(["coinflip", "toss"]))
async def coin_flip(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in active_coinflips:
        await message.reply_text(
            "🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯</b>\n\n"
            "<blockquote>⏳ Your previous flip is still processing! Please wait.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return
        
    args = message.command
    if len(args) < 3:
        await message.reply_text(
            "🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯 𝖦𝖠𝖬𝖤</b>\n\n"
            "<blockquote>🎮 <b>How to Play:</b>\n"
            "Use <code>/coinflip &lt;amount&gt; &lt;heads/tails&gt;</code>\n"
            "Example: <code>/coinflip 500 heads</code>\n\n"
            "⚠️ Min bet: 100 | Max bet: 50,000</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    # Parse and validate amount
    try:
        amount = int(args[1])
        if amount < 100 or amount > 50000:
            await message.reply_text(
                "🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯</b>\n\n"
                "<blockquote>❌ Bet amount must be between 100 and 50,000 coins!</blockquote>",
                parse_mode=enums.ParseMode.HTML,
                quote=True
            )
            return
    except ValueError:
        await message.reply_text(
            "🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯</b>\n\n"
            "<blockquote>❌ Please enter a valid number for the bet amount!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    # Parse and validate choice
    choice_input = args[2].lower()
    if choice_input in ["heads", "head", "h"]:
        choice = "Heads"
    elif choice_input in ["tails", "tail", "t"]:
        choice = "Tails"
    else:
        await message.reply_text(
            "🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯</b>\n\n"
            "<blockquote>❌ Invalid choice! Choose heads (h) or tails (t).</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    # Check database and fetch user balance
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or user_data.get("balance", 0) < amount:
        await message.reply_text(
            "🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯</b>\n\n"
            "<blockquote>❌ Insufficient balance to place this bet!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    # Lock the user
    active_coinflips.add(user_id)
    
    try:
        # Deduct bet amount upfront
        await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -amount}})
        
        # Initial message
        status_msg = await message.reply_text(
            f"🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯 𝖳𝖮𝖲𝖲</b>\n\n"
            f"👤 <b>Player:</b> {message.from_user.mention}\n"
            f"<blockquote>💰 <b>Bet:</b> {amount} coins\n"
            f"🎯 <b>Prediction:</b> {choice}\n\n"
            f"🌀 <i>Spinning the coin in the air...</i></blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        
        # Wait for suspense
        await asyncio.sleep(2)
        
        # Determine outcome
        result = random.choice(["Heads", "Tails"])
        won = (choice == result)
        
        if won:
            winnings = amount * 2
            # Add winnings
            updated_user = await user_collection.find_one_and_update(
                {"id": user_id},
                {"$inc": {"balance": winnings}},
                return_document=True
            )
            new_balance = updated_user.get("balance", 0)
            
            await status_msg.edit_text(
                f"🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯 𝖳𝖮𝖲𝖲</b>\n\n"
                f"👤 <b>Player:</b> {message.from_user.mention}\n"
                f"<blockquote>🎯 <b>Prediction:</b> {choice}\n"
                f"✨ <b>Result:</b> Landed on {result}! ✅\n\n"
                f"🎉 <b>𝖸𝖮𝖴 𝖶𝖮𝖭!</b>\n"
                f"💰 <b>Earnings:</b> +{amount} coins\n"
                f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            # Fetch balance to display
            updated_user = await user_collection.find_one({"id": user_id})
            new_balance = updated_user.get("balance", 0)
            
            await status_msg.edit_text(
                f"🪙 <b>𝖢𝖮𝖨𝖭𝖥𝖫𝖨𝖯 𝖳𝖮𝖲𝖲</b>\n\n"
                f"👤 <b>Player:</b> {message.from_user.mention}\n"
                f"<blockquote>🎯 <b>Prediction:</b> {choice}\n"
                f"✨ <b>Result:</b> Landed on {result}! ❌\n\n"
                f"😭 <b>𝖸𝖮𝖴 𝖫𝖮𝖲𝖳!</b>\n"
                f"💸 <b>Loss:</b> -{amount} coins\n"
                f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            
    except Exception as e:
        print(f"Error in coinflip: {e}")
        try:
            await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}})
            await message.reply_text("⚠️ An error occurred during the flip. Your bet has been refunded.", quote=True)
        except Exception:
            pass
    finally:
        active_coinflips.remove(user_id)
