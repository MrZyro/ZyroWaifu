# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

# TEAMZYRO/commands/jackpot.py
from TEAMZYRO import app, user_collection
from pyrogram import filters, enums
from pymongo import ReturnDocument
import datetime

@app.on_message(filters.command("jackpot"))
async def basket(bot, message):
    user_id = message.from_user.id
    today = datetime.date.today()

    # Check if user exists in the database
    user_data = await user_collection.find_one({"id": user_id})
    if not user_data:
        # Initialize user data
        user_data = {
            "id": user_id,
            "username": message.from_user.username,
            "first_name": message.from_user.first_name,
            "balance": 0,
            "last_played": None,
            "plays_today": 0,
            "characters": []
        }
        await user_collection.insert_one(user_data)

    # Check play limits
    last_played = user_data.get("last_played")
    plays_today = user_data.get("plays_today", 0)

    if last_played == str(today) and plays_today >= 2:
        await message.reply_text(
            f"🎰 <b>𝖩𝖠𝖢𝖪𝖯𝖮𝖳</b>\n\n"
            f"<blockquote>❌ You can only play the jackpot twice per day. Try again tomorrow!</blockquote>",
            parse_mode=enums.ParseMode.HTML
        )
        return

    # Send dice and calculate score
    dice_message = await bot.send_dice(message.chat.id, "🎰")
    dice_score = dice_message.dice.value

    # Calculate rewards
    if dice_score == 64:
        coins_earned = 2000
    else:
        coins_earned = 5 * dice_score

    # Construct update query
    if last_played == str(today):
        update_query = {
            "$set": {"last_played": str(today)},
            "$inc": {"balance": coins_earned, "plays_today": 1}
        }
    else:
        update_query = {
            "$set": {"last_played": str(today), "plays_today": 1},
            "$inc": {"balance": coins_earned}
        }

    # Update user's balance and play count
    updated_user = await user_collection.find_one_and_update(
        {"id": user_id},
        update_query,
        return_document=ReturnDocument.AFTER
    )

    # Send response
    await message.reply_text(
        f"🎰 <b>𝖩𝖠𝖢𝖪𝖯𝖮𝖳 𝖱𝖤𝖲𝖴𝖫𝖳</b>\n\n"
        f"👤 <b>Player:</b> {message.from_user.mention}\n"
        f"<blockquote>🎲 <b>Dice Score:</b> {dice_score}\n"
        f"💰 <b>Earned:</b> +{coins_earned} coins 🎉\n"
        f"💳 <b>New Balance:</b> {updated_user['balance']} coins</blockquote>",
        quote=True,
        parse_mode=enums.ParseMode.HTML
    )
