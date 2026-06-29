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

active_bj_games = {}
processing_bj_clicks = set()

SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_NAMES = {
    11: "J",
    12: "Q",
    13: "K",
    14: "A"
}

def get_card_name(value):
    return CARD_NAMES.get(value, str(value))

def calculate_score(hand):
    score = 0
    aces = 0
    for card_val, _ in hand:
        if card_val == 14:
            aces += 1
            score += 11
        elif card_val >= 11:
            score += 10
        else:
            score += card_val
            
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
        
    return score

def draw_card(deck):
    if not deck:
        deck.extend([(val, suit) for val in range(2, 15) for suit in SUITS])
        random.shuffle(deck)
    return deck.pop()

def get_hand_display(hand, hide_first=False):
    displays = []
    for i, (val, suit) in enumerate(hand):
        if i == 0 and hide_first:
            displays.append("[ ❓ Hidden Card ]")
        else:
            displays.append(f"<b>{get_card_name(val)}{suit}</b>")
    return " | ".join(displays)

def generate_bj_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Hit 🟢", callback_data=f"bj_hit_{user_id}"),
            InlineKeyboardButton("Stand 🔴", callback_data=f"bj_stand_{user_id}")
        ]
    ])

@app.on_message(filters.command(["blackjack", "bj"]))
async def start_blackjack(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in active_bj_games:
        await message.reply_text(
            "🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪</b>\n\n"
            "<blockquote>⚠️ You already have an active Blackjack game session! Finish that game first.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    args = message.command
    if len(args) < 2:
        await message.reply_text(
            "🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖳𝖠𝖡𝖫𝖤</b>\n\n"
            "<blockquote>🎮 <b>How to Play:</b>\n"
            "Start the game using <code>/bj &lt;amount&gt;</code>\n"
            "Get card score close to 21 without exceeding it!\n\n"
            "🏆 <b>Payouts:</b>\n"
            "• Win: 2.0x | Blackjack: 2.5x | Push: Refund\n\n"
            "⚠️ Min bet: 100 | Max bet: 50,000</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    try:
        amount = int(args[1])
        if amount < 100 or amount > 50000:
            await message.reply_text(
                "🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪</b>\n\n"
                "<blockquote>❌ Bet amount must be between 100 and 50,000 coins!</blockquote>",
                parse_mode=enums.ParseMode.HTML,
                quote=True
            )
            return
    except ValueError:
        await message.reply_text(
            "🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪</b>\n\n"
            "<blockquote>❌ Please enter a valid number for the bet amount!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or user_data.get("balance", 0) < amount:
        await message.reply_text(
            "🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪</b>\n\n"
            "<blockquote>❌ Insufficient balance to place this bet!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    try:
        await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -amount}})
        
        deck = [(val, suit) for val in range(2, 15) for suit in SUITS]
        random.shuffle(deck)
        
        player_hand = [draw_card(deck), draw_card(deck)]
        dealer_hand = [draw_card(deck), draw_card(deck)]
        
        player_score = calculate_score(player_hand)
        
        if player_score == 21:
            dealer_score = calculate_score(dealer_hand)
            if dealer_score == 21:
                await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}})
                await message.reply_text(
                    f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖯𝖴𝖲𝖧</b>\n\n"
                    f"<blockquote>👤 <b>Player Hand:</b> {get_hand_display(player_hand)} (Score: 21)\n"
                    f"🤖 <b>Dealer Hand:</b> {get_hand_display(dealer_hand)} (Score: 21)\n\n"
                    f"👔 <b>Push (Tie)!</b> Both landed Natural Blackjack. Your bet of {amount} coins was refunded.</blockquote>",
                    parse_mode=enums.ParseMode.HTML,
                    quote=True
                )
            else:
                winnings = int(amount * 2.5)
                updated_user = await user_collection.find_one_and_update(
                    {"id": user_id},
                    {"$inc": {"balance": winnings}},
                    return_document=True
                )
                new_balance = updated_user.get("balance", 0)
                
                await message.reply_text(
                    f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖶𝖨𝖭!</b>\n\n"
                    f"<blockquote>👤 <b>Player Hand:</b> {get_hand_display(player_hand)} (Score: 21)\n"
                    f"🤖 <b>Dealer Hand:</b> {get_hand_display(dealer_hand)} (Score: {calculate_score(dealer_hand)})\n\n"
                    f"🎉 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪!</b> You scored perfect 21!\n"
                    f"💰 <b>Earnings:</b> +{winnings - amount} coins\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                    parse_mode=enums.ParseMode.HTML,
                    quote=True
                )
            return
            
        active_bj_games[user_id] = {
            "deck": deck,
            "player_hand": player_hand,
            "dealer_hand": dealer_hand,
            "bet": amount
        }
        
        await message.reply_text(
            f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖳𝖠𝖡𝖫𝖤</b>\n\n"
            f"👤 <b>Your Hand:</b>\n"
            f"<blockquote>• {get_hand_display(player_hand)} (Score: {player_score})</blockquote>\n"
            f"🤖 <b>Dealer's Hand:</b>\n"
            f"<blockquote>• {get_hand_display(dealer_hand, hide_first=True)} (Score: Visible card)</blockquote>\n"
            f"Choose your move:",
            reply_markup=generate_bj_keyboard(user_id),
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        
    except Exception as e:
        print(f"Error starting Blackjack game: {e}")
        try:
            await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}})
            await message.reply_text("❌ An error occurred starting the game. Refunded.", quote=True)
        except Exception:
            pass

@app.on_callback_query(filters.regex(r"^bj_(\S+)_(\d+)$"))
async def handle_bj_click(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("_")
    action, player_id = data[1], int(data[2])
    
    if user_id != player_id:
        await callback_query.answer("This is not your game session!", show_alert=True)
        return

    if user_id not in active_bj_games:
        await callback_query.answer("Game expired! Start a new one using /bj.", show_alert=True)
        await callback_query.message.delete()
        return

    if user_id in processing_bj_clicks:
        await callback_query.answer("Processing...", show_alert=True)
        return
        
    processing_bj_clicks.add(user_id)
    
    try:
        game = active_bj_games[user_id]
        deck = game["deck"]
        player_hand = game["player_hand"]
        dealer_hand = game["dealer_hand"]
        amount = game["bet"]
        
        if action == "hit":
            player_hand.append(draw_card(deck))
            player_score = calculate_score(player_hand)
            
            if player_score > 21:
                del active_bj_games[user_id]
                
                updated_user = await user_collection.find_one({"id": user_id})
                new_balance = updated_user.get("balance", 0)
                
                await callback_query.message.edit_text(
                    f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖳𝖠𝖡𝖫𝖤</b>\n\n"
                    f"👤 <b>Your Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(player_hand)} (Score: {player_score})</blockquote>\n"
                    f"🤖 <b>Dealer's Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(dealer_hand)} (Score: {calculate_score(dealer_hand)})</blockquote>\n\n"
                    f"<blockquote>💥 <b>𝖡𝖴𝖲𝖳!</b> Exceeded 21. Lost {amount} coins!\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await callback_query.message.edit_text(
                    f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖳𝖠𝖡𝖫𝖤</b>\n\n"
                    f"👤 <b>Your Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(player_hand)} (Score: {player_score})</blockquote>\n"
                    f"🤖 <b>Dealer's Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(dealer_hand, hide_first=True)} (Score: Visible card)</blockquote>\n"
                    f"Choose your move:",
                    reply_markup=generate_bj_keyboard(user_id),
                    parse_mode=enums.ParseMode.HTML
                )
                await callback_query.answer("Card drawn!", show_alert=False)
                
        elif action == "stand":
            del active_bj_games[user_id]
            
            player_score = calculate_score(player_hand)
            dealer_score = calculate_score(dealer_hand)
            
            while dealer_score < 17:
                dealer_hand.append(draw_card(deck))
                dealer_score = calculate_score(dealer_hand)
                
            won = False
            tie = False
            dealer_busted = (dealer_score > 21)
            
            if dealer_busted:
                won = True
            elif player_score > dealer_score:
                won = True
            elif player_score == dealer_score:
                tie = True
                
            if tie:
                updated_user = await user_collection.find_one_and_update(
                    {"id": user_id},
                    {"$inc": {"balance": amount}},
                    return_document=True
                )
                new_balance = updated_user.get("balance", 0)
                
                await callback_query.message.edit_text(
                    f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖳𝖠𝖡𝖫𝖤</b>\n\n"
                    f"👤 <b>Your Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(player_hand)} (Score: {player_score})</blockquote>\n"
                    f"🤖 <b>Dealer's Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(dealer_hand)} (Score: {dealer_score})</blockquote>\n\n"
                    f"<blockquote>👔 <b>𝖯𝖴𝖲𝖧!</b> Both scored {player_score}. Bet refunded.\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                    parse_mode=enums.ParseMode.HTML
                )
                
            elif won:
                winnings = amount * 2
                updated_user = await user_collection.find_one_and_update(
                    {"id": user_id},
                    {"$inc": {"balance": winnings}},
                    return_document=True
                )
                new_balance = updated_user.get("balance", 0)
                
                dealer_busted_text = " 💥 (Busted)" if dealer_busted else ""
                
                await callback_query.message.edit_text(
                    f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖳𝖠𝖡𝖫𝖤</b>\n\n"
                    f"👤 <b>Your Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(player_hand)} (Score: {player_score})</blockquote>\n"
                    f"🤖 <b>Dealer's Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(dealer_hand)} (Score: {dealer_score}{dealer_busted_text})</blockquote>\n\n"
                    f"<blockquote>🎉 <b>𝖸𝖮𝖴 𝖶𝖮𝖭!</b>\n"
                    f"💰 <b>Earnings:</b> +{amount} coins (Payout: {winnings})\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                    parse_mode=enums.ParseMode.HTML
                )
                
            else:
                updated_user = await user_collection.find_one({"id": user_id})
                new_balance = updated_user.get("balance", 0)
                
                await callback_query.message.edit_text(
                    f"🃏 <b>𝖡𝖫𝖠𝖢𝖪𝖩𝖠𝖢𝖪 𝖳𝖠𝖡𝖫𝖤</b>\n\n"
                    f"👤 <b>Your Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(player_hand)} (Score: {player_score})</blockquote>\n"
                    f"🤖 <b>Dealer's Hand:</b>\n"
                    f"<blockquote>• {get_hand_display(dealer_hand)} (Score: {dealer_score})</blockquote>\n\n"
                    f"<blockquote>😭 <b>𝖸𝖮𝖴 𝖫𝖮𝖲𝖳!</b> Dealer wins.\n"
                    f"💸 <b>Loss:</b> -{amount} coins\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins</blockquote>",
                    parse_mode=enums.ParseMode.HTML
                )
            
            await callback_query.answer("Stand complete!", show_alert=False)

    except Exception as e:
        print(f"Error handling Blackjack click: {e}")
        await callback_query.answer("Error processing click.", show_alert=True)
    finally:
        if user_id in processing_bj_clicks:
            processing_bj_clicks.remove(user_id)
