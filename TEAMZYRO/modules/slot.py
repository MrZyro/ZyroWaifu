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

# Concurrency lock to prevent spam and double bets
active_slots = set()

# Reel emojis
SLOT_EMOJIS = ['🍒', '🍋', '🍇', '🔔', '💎', '🎰']

@app.on_message(filters.command(["slot", "slots"]))
async def slot_machine(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in active_slots:
        await message.reply_text(
            "🎰 <b>𝖲𝖫𝖮𝖳𝖲</b>\n\n"
            "<blockquote>⏳ Your previous slot spin is still processing! Please wait.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    args = message.command
    if len(args) < 2:
        await message.reply_text(
            "🎰 <b>𝖲𝖫𝖮𝖳 𝖬𝖠𝖢𝖧𝖨𝖭𝖤</b>\n\n"
            "<blockquote>🎮 <b>How to Play:</b>\n"
            "Use <code>/slot &lt;amount&gt;</code>\n"
            "Example: <code>/slot 500</code>\n\n"
            "🏆 <b>Payout Multipliers:</b>\n"
            "• 3 matches: <b>5.0x payout</b>\n"
            "• 2 matches: <b>1.5x payout</b>\n\n"
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
                "🎰 <b>𝖲𝖫𝖮𝖳𝖲</b>\n\n"
                "<blockquote>❌ Bet amount must be between 100 and 50,000 coins!</blockquote>",
                parse_mode=enums.ParseMode.HTML,
                quote=True
            )
            return
    except ValueError:
        await message.reply_text(
            "🎰 <b>𝖲𝖫𝖮𝖳𝖲</b>\n\n"
            "<blockquote>❌ Please enter a valid number for the bet amount!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    # Check database and fetch user balance
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or user_data.get("balance", 0) < amount:
        await message.reply_text(
            "🎰 <b>𝖲𝖫𝖮𝖳𝖲</b>\n\n"
            "<blockquote>❌ Insufficient balance to place this bet!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    # Lock the user
    active_slots.add(user_id)
    
    try:
        # Deduct bet amount upfront
        await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -amount}})
        
        # Initial message showing reels spinning
        status_msg = await message.reply_text(
            f"🎰 <b>𝖲𝖫𝖮𝖳 𝖬𝖠𝖢𝖧𝖨𝖭𝖤</b>\n\n"
            f"👤 <b>Player:</b> {message.from_user.mention}\n"
            f"<blockquote>💰 <b>Bet:</b> {amount} coins\n\n"
            f"🌀 <b>[ 🎰 | 🎰 | 🎰 ]</b>\n\n"
            f"<i>Rolling the reels...</i></blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        
        # Sleep for slot animation effect
        await asyncio.sleep(1.5)
        
        # Roll results
        reel1 = random.choice(SLOT_EMOJIS)
        reel2 = random.choice(SLOT_EMOJIS)
        reel3 = random.choice(SLOT_EMOJIS)
        
        # Analyze outcome
        reels = [reel1, reel2, reel3]
        unique_count = len(set(reels))
        
        if unique_count == 1:
            multiplier = 5.0
            winnings = int(amount * multiplier)
            win_msg = f"🎉 <b>𝖩𝖠𝖢𝖪𝖯𝖮𝖳!</b> All three matched! (5.0x)"
        elif unique_count == 2:
            multiplier = 1.5
            winnings = int(amount * multiplier)
            win_msg = f"🎉 <b>𝖬𝖠𝖳𝖢𝖧!</b> Two emojis matched! (1.5x)"
        else:
            multiplier = 0.0
            winnings = 0
            win_msg = f"😭 <b>𝖭𝖮 𝖬𝖠𝖳𝖢𝖧!</b> Better luck next time!"

        if winnings > 0:
            updated_user = await user_collection.find_one_and_update(
                {"id": user_id},
                {"$inc": {"balance": winnings}},
                return_document=True
            )
            new_balance = updated_user.get("balance", 0)
            net_change = winnings - amount
            
            await status_msg.edit_text(
                f"🎰 <b>𝖲𝖫𝖮𝖳 𝖬𝖠𝖢𝖧𝖨𝖭𝖤</b>\n\n"
                f"👤 <b>Player:</b> {message.from_user.mention}\n"
                f"<blockquote>✨ <b>[ {reel1} | {reel2} | {reel3} ]</b>\n\n"
                f"{win_msg}\n"
                f"💰 <b>Net Gain:</b> +{net_change} coins (Payout: {winnings})\n"
                f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            updated_user = await user_collection.find_one({"id": user_id})
            new_balance = updated_user.get("balance", 0)
            
            await status_msg.edit_text(
                f"🎰 <b>𝖲𝖫𝖮𝖳 𝖬𝖠𝖢𝖧𝖨𝖭𝖤</b>\n\n"
                f"👤 <b>Player:</b> {message.from_user.mention}\n"
                f"<blockquote>✨ <b>[ {reel1} | {reel2} | {reel3} ]</b>\n\n"
                f"{win_msg}\n"
                f"💸 <b>Net Loss:</b> -{amount} coins\n"
                f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            
    except Exception as e:
        print(f"Error in slots: {e}")
        try:
            await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}})
            await message.reply_text("⚠️ An error occurred during the spin. Your bet has been refunded.", quote=True)
        except Exception:
            pass
    finally:
        active_slots.remove(user_id)
