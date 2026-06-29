# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from TEAMZYRO import app, user_collection
import random
import asyncio

active_hl_games = {}
processing_hl_clicks = set()

SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_NAMES = {
    11: "Jack",
    12: "Queen",
    13: "King",
    14: "Ace"
}

def get_card_display(value, suit):
    name = CARD_NAMES.get(value, str(value))
    return f"<b>{name} of {suit}</b>"

def draw_card():
    value = random.randint(2, 14)
    suit = random.choice(SUITS)
    return value, suit

def generate_hl_keyboard(user_id, current_value):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Higher 📈", callback_data=f"hl_higher_{user_id}"),
            InlineKeyboardButton("Lower 📉", callback_data=f"hl_lower_{user_id}")
        ],
        [
            InlineKeyboardButton(f"💰 Cashout ({current_value} coins)", callback_data=f"hl_cashout_{user_id}")
        ]
    ])

@app.on_message(filters.command(["hl", "highlow"]))
async def start_hl(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in active_hl_games:
        await message.reply_text(
            "🃏 <b>𝖧𝖨𝖦𝖧 𝖫𝖮𝖶</b>\n\n"
            "<blockquote>⚠️ You already have an active Higher or Lower game session! Finished/cashout that game first.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    args = message.command
    if len(args) < 2:
        await message.reply_text(
            "🃏 <b>𝖧𝖨𝖦𝖧𝖤𝖱 𝖮𝖱 𝖫𝖮𝖶𝖤𝖱</b>\n\n"
            "<blockquote>🎮 <b>How to Play:</b>\n"
            "Start the game using <code>/hl &lt;amount&gt;</code>\n"
            "Guess whether the next card will be Higher/Lower than current!\n\n"
            "🏆 <b>Multipliers:</b>\n"
            "• Streak 1: 1.4x | Streak 2: 1.8x | Streak 3: 2.2x (+0.4x each)\n\n"
            "⚠️ Min bet: 100 | Max bet: 50,000</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    try:
        amount = int(args[1])
        if amount < 100 or amount > 50000:
            await message.reply_text(
                "🃏 <b>𝖧𝖨𝖦𝖧 𝖫𝖮𝖶</b>\n\n"
                "<blockquote>❌ Bet amount must be between 100 and 50,000 coins!</blockquote>",
                parse_mode=enums.ParseMode.HTML,
                quote=True
            )
            return
    except ValueError:
        await message.reply_text(
            "🃏 <b>𝖧𝖨𝖦𝖧 𝖫𝖮𝖶</b>\n\n"
            "<blockquote>❌ Please enter a valid number for the bet amount!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or user_data.get("balance", 0) < amount:
        await message.reply_text(
            "🃏 <b>𝖧𝖨𝖦𝖧 𝖫𝖮𝖶</b>\n\n"
            "<blockquote>❌ Insufficient balance to place this bet!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    try:
        await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -amount}})
        card_val, card_suit = draw_card()
        
        active_hl_games[user_id] = {
            "card_val": card_val,
            "card_suit": card_suit,
            "streak": 0,
            "bet": amount,
            "current_value": amount
        }
        
        card_str = get_card_display(card_val, card_suit)
        
        await message.reply_text(
            f"🃏 <b>𝖧𝖨𝖦𝖧𝖤𝖱 𝖮𝖱 𝖫𝖮𝖶𝖤𝖱</b>\n\n"
            f"👤 <b>Player:</b> {message.from_user.mention}\n"
            f"<blockquote>💰 <b>Starting Bet:</b> {amount} coins\n"
            f"📈 <b>Current Win Streak:</b> 0\n"
            f"💸 <b>Current Value:</b> {amount} coins\n\n"
            f"🎴 <b>Current Card:</b> {card_str}\n\n"
            f"Guess if the next card will be Higher or Lower!</blockquote>",
            reply_markup=generate_hl_keyboard(user_id, amount),
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        
    except Exception as e:
        print(f"Error starting Higher/Lower game: {e}")
        try:
            await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}})
            await message.reply_text("❌ An error occurred starting the game. Refunded.", quote=True)
        except Exception:
            pass

@app.on_callback_query(filters.regex(r"^hl_(\S+)_(\d+)$"))
async def handle_hl_click(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("_")
    action, player_id = data[1], int(data[2])
    
    if user_id != player_id:
        await callback_query.answer("This is not your game session!", show_alert=True)
        return

    if user_id not in active_hl_games:
        await callback_query.answer("Game expired! Start a new one using /hl.", show_alert=True)
        await callback_query.message.delete()
        return

    if user_id in processing_hl_clicks:
        await callback_query.answer("Processing...", show_alert=True)
        return
        
    processing_hl_clicks.add(user_id)
    
    try:
        game = active_hl_games[user_id]
        
        if action == "cashout":
            winnings = game["current_value"]
            del active_hl_games[user_id]
            
            updated_user = await user_collection.find_one_and_update(
                {"id": user_id},
                {"$inc": {"balance": winnings}},
                return_document=True
            )
            new_balance = updated_user.get("balance", 0)
            net_profit = winnings - game["bet"]
            
            await callback_query.message.edit_text(
                f"🃏 <b>𝖧𝖨𝖦𝖧𝖤𝖱 𝖮𝖱 𝖫𝖮𝖶𝖤𝖱</b>\n\n"
                f"👤 <b>Player:</b> {callback_query.from_user.mention}\n"
                f"<blockquote>📈 <b>Final Streak:</b> {game['streak']}\n"
                f"💰 <b>Cashout Payout:</b> {winnings} coins\n"
                f"✨ <b>Net Profit:</b> +{net_profit} coins\n"
                f"💳 <b>New Balance:</b> {new_balance} coins\n\n"
                f"✅ Game closed successfully!</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            return
            
        old_val = game["card_val"]
        new_val, new_suit = draw_card()
        
        correct = False
        tie = (old_val == new_val)
        
        if not tie:
            if action == "higher" and new_val > old_val:
                correct = True
            elif action == "lower" and new_val < old_val:
                correct = True

        if tie:
            game["card_val"] = new_val
            game["card_suit"] = new_suit
            card_str = get_card_display(new_val, new_suit)
            
            await callback_query.answer("It's a Tie! Swapped card.", show_alert=False)
            await callback_query.message.edit_text(
                f"🃏 <b>𝖧𝖨𝖦𝖧𝖤𝖱 𝖮𝖱 𝖫𝖮𝖶𝖤𝖱</b>\n\n"
                f"👤 <b>Player:</b> {callback_query.from_user.mention}\n"
                f"<blockquote>💰 <b>Starting Bet:</b> {game['bet']} coins\n"
                f"📈 <b>Current Win Streak:</b> {game['streak']}\n"
                f"💸 <b>Current Value:</b> {game['current_value']} coins\n\n"
                f"🎴 <b>Current Card:</b> {card_str}\n\n"
                f"👔 <b>Tie Card Swapped!</b> Guess Higher or Lower!</blockquote>",
                reply_markup=generate_hl_keyboard(user_id, game['current_value']),
                parse_mode=enums.ParseMode.HTML
            )
            
        elif correct:
            game["streak"] += 1
            multiplier = 1.0 + (game["streak"] * 0.4)
            game["current_value"] = int(game["bet"] * multiplier)
            game["card_val"] = new_val
            game["card_suit"] = new_suit
            card_str = get_card_display(new_val, new_suit)
            
            await callback_query.answer("Correct! Streak increased!", show_alert=False)
            await callback_query.message.edit_text(
                f"🃏 <b>𝖧𝖨𝖦𝖧𝖤𝖱 𝖮𝖱 𝖫𝖮𝖶𝖤𝖱</b>\n\n"
                f"👤 <b>Player:</b> {callback_query.from_user.mention}\n"
                f"<blockquote>💰 <b>Starting Bet:</b> {game['bet']} coins\n"
                f"📈 <b>Current Win Streak:</b> {game['streak']} 🔥\n"
                f"💸 <b>Current Value:</b> {game['current_value']} coins\n\n"
                f"🎴 <b>Current Card:</b> {card_str}\n\n"
                f"✅ <b>Correct!</b> Guess Higher or Lower!</blockquote>",
                reply_markup=generate_hl_keyboard(user_id, game['current_value']),
                parse_mode=enums.ParseMode.HTML
            )
            
        else:
            del active_hl_games[user_id]
            card_str = get_card_display(new_val, new_suit)
            
            updated_user = await user_collection.find_one({"id": user_id})
            new_balance = updated_user.get("balance", 0)
            
            await callback_query.message.edit_text(
                f"🃏 <b>𝖧𝖨𝖦𝖧𝖤𝖱 𝖮𝖱 𝖫𝖮𝖶𝖤𝖱</b>\n\n"
                f"👤 <b>Player:</b> {callback_query.from_user.mention}\n"
                f"<blockquote>💰 <b>Starting Bet:</b> {game['bet']} coins\n"
                f"📉 <b>Final Streak:</b> {game['streak']}\n"
                f"🎴 <b>Drawn Card:</b> {card_str}\n\n"
                f"❌ <b>Busted! Game Over.</b> You lost your bet of {game['bet']} coins!\n"
                f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )

    except Exception as e:
        print(f"Error handling Higher/Lower click: {e}")
        await callback_query.answer("Error processing click.", show_alert=True)
    finally:
        if user_id in processing_hl_clicks:
            processing_hl_clicks.remove(user_id)
