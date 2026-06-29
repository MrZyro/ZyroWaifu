# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import os
import random
import time
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from TEAMZYRO import app, db, user_collection, require_power, application

# Database collections
ox_games = db["ox_games"]
ox_stats = db["ox_stats"]

# Game limits
MIN_BET = 100
MAX_BET = 100000

# Win check utility
def check_winner(board):
    # Rows check
    for r in range(3):
        if board[r][0] != "" and board[r][0] == board[r][1] == board[r][2]:
            return board[r][0]
    # Columns check
    for c in range(3):
        if board[0][c] != "" and board[0][c] == board[1][c] == board[2][c]:
            return board[0][c]
    # Diagonals check
    if board[0][0] != "" and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    if board[0][2] != "" and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return None

# Board full check utility
def is_board_full(board):
    for r in range(3):
        for c in range(3):
            if board[r][c] == "":
                return False
    return True

# Database balance helpers
async def get_balance(user_id: int) -> int:
    user_data = await user_collection.find_one({'id': user_id}, {'balance': 1})
    if user_data:
        return user_data.get('balance', 0)
    return 0

async def update_balance(user_id: int, amount: int):
    await user_collection.update_one(
        {'id': user_id},
        {'$inc': {'balance': amount}},
        upsert=True
    )

# Database stats helpers
async def record_game_result(winner_id: int, loser_id: int, winner_name: str, loser_name: str):
    await ox_stats.update_one(
        {"_id": winner_id},
        {"$set": {"first_name": winner_name}, "$inc": {"wins": 1}},
        upsert=True
    )
    await ox_stats.update_one(
        {"_id": loser_id},
        {"$set": {"first_name": loser_name}, "$inc": {"losses": 1}},
        upsert=True
    )

async def record_game_draw(p1_id: int, p2_id: int, p1_name: str, p2_name: str):
    for pid, pname in [(p1_id, p1_name), (p2_id, p2_name)]:
        await ox_stats.update_one(
            {"_id": pid},
            {"$set": {"first_name": pname}, "$inc": {"draws": 1}},
            upsert=True
        )

# Keyboard generator helper
def make_board_keyboard(game_id: str, board: list) -> InlineKeyboardMarkup:
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            val = board[r][c]
            emoji = "⬜"
            if val == "X":
                emoji = "❌"
            elif val == "O":
                emoji = "⭕"
            row.append(InlineKeyboardButton(emoji, callback_data=f"ox_play_{game_id}_{r}_{c}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


# ── COMMANDS ─────────────────────────────────────────────────────────

@app.on_message(filters.command("ox"))
async def host_ox_game(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    args = message.command
    if len(args) < 2:
        await message.reply_text("❌ **Usage:** `/ox <bet_amount>`\nExample: `/ox 1000`")
        return

    try:
        bet = int(args[1])
    except ValueError:
        await message.reply_text("❌ **Bet amount must be a positive number!**")
        return

    if bet < MIN_BET or bet > MAX_BET:
        await message.reply_text(f"❌ **Bet amount must be between {MIN_BET:,} and {MAX_BET:,} coins!**")
        return

    # Check if user already has an active lobby or game running
    existing_lobby = await ox_games.find_one({
        "status": {"$in": ["lobby", "playing"]},
        "$or": [{"player1": user_id}, {"player2": user_id}]
    })
    if existing_lobby:
        await message.reply_text("❌ **You already have an active game or lobby!**\nPlease finish it first.")
        return

    # Check host balance
    balance = await get_balance(user_id)
    if balance < bet:
        await message.reply_text(f"❌ **You do not have enough coins to bet {bet:,}!**\nYour balance: `{balance:,}` coins.")
        return

    # Lock host balance
    await update_balance(user_id, -bet)

    # Insert game state
    game_id = str(int(time.time() * 1000))
    game_data = {
        "game_id": game_id,
        "player1": user_id,
        "player1_name": first_name,
        "player2": None,
        "player2_name": None,
        "bet": bet,
        "prize_pool": bet * 2,
        "symbol_x": None,
        "symbol_o": None,
        "turn": None,
        "board": [
            ["", "", ""],
            ["", "", ""],
            ["", "", ""]
        ],
        "status": "lobby",
        "created_at": time.time(),
        "last_move_at": time.time(),
        "chat_id": message.chat.id,
        "message_id": None
    }
    await ox_games.insert_one(game_data)
    
    lobby_text = (
        "🎮 <b>Tic Tac Toe Match</b>\n\n"
        f"<b>Host:</b> {first_name}\n"
        f"<b>Bet:</b> <code>{bet:,}</code> Coins\n\n"
        "⏳ <i>Waiting for opponent...</i>"
    )
    
    join_buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("🎮 Join Game", callback_data=f"join_ox_{game_id}"),
        InlineKeyboardButton("❌ Cancel Match", callback_data=f"cancel_ox_{game_id}")
    ]])

    sent_message = await message.reply_text(
        text=lobby_text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=join_buttons
    )

    # Save message_id to game state
    await ox_games.update_one(
        {"game_id": game_id},
        {"$set": {"message_id": sent_message.id}}
    )


@app.on_message(filters.command("oxactive"))
async def active_matches_handler(client, message):
    count = await ox_games.count_documents({"status": "playing"})
    await message.reply_text(f"🎮 **Active Matches:** {count}")


@app.on_message(filters.command("oxstats"))
async def stats_handler(client, message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    target_id = user_id
    target_name = first_name

    if len(message.command) > 1:
        arg = message.command[1]
        if arg.isdigit():
            target_id = int(arg)
            user_data = await user_collection.find_one({'id': target_id})
            if user_data:
                target_name = user_data.get('first_name', str(target_id))
            else:
                target_name = str(target_id)
        elif message.reply_to_message:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name
        else:
            clean_username = arg.replace("@", "")
            user_data = await user_collection.find_one({'username': clean_username})
            if user_data:
                target_id = user_data.get('id')
                target_name = user_data.get('first_name', clean_username)
            else:
                await message.reply_text("❌ **User not found in database!**")
                return

    stats = await ox_stats.find_one({"_id": target_id})
    if not stats:
        stats = {"wins": 0, "losses": 0, "draws": 0}

    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    draws = stats.get("draws", 0)
    total = wins + losses + draws
    win_rate = (wins / total * 100) if total > 0 else 0

    stats_text = (
        "🎮 <b>Tic Tac Toe Stats</b>\n\n"
        f"👤 <b>Player:</b> {target_name}\n"
        f"🏆 <b>Wins:</b> {wins}\n"
        f"❌ <b>Losses:</b> {losses}\n"
        f"🤝 <b>Draws:</b> {draws}\n"
        f"📊 <b>Win Rate:</b> {win_rate:.1f}%"
    )
    await message.reply_text(stats_text, parse_mode=enums.ParseMode.HTML)


@app.on_message(filters.command("oxtop"))
async def top_players_handler(client, message):
    cursor = ox_stats.find().sort("wins", -1).limit(10)
    top_list = await cursor.to_list(length=10)
    
    if not top_list:
        await message.reply_text("🏆 **No Tic Tac Toe stats recorded yet!**")
        return

    top_text = "🏆 <b>Top OX Players</b>\n\n"
    for idx, player in enumerate(top_list, 1):
        name = player.get("first_name", "Unknown")
        wins = player.get("wins", 0)
        top_text += f"{idx}. {name} - {wins} Wins\n"
        
    await message.reply_text(top_text, parse_mode=enums.ParseMode.HTML)


# ── CALLBACK HANDLERS ──────────────────────────────────────────────────

@app.on_callback_query(filters.regex(r"^join_ox_(\w+)"))
async def join_ox_callback(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    game_id = callback_query.data.split("_")[2]

    game = await ox_games.find_one({"game_id": game_id})
    if not game:
        await callback_query.answer("Game not found!", show_alert=True)
        return

    if game["status"] != "lobby":
        await callback_query.answer("This game has already started or been cancelled!", show_alert=True)
        return

    if game["player1"] == user_id:
        await callback_query.answer("You cannot join your own game!", show_alert=True)
        return

    # Verify if user has another active lobby or playing game
    existing_lobby = await ox_games.find_one({
        "status": {"$in": ["lobby", "playing"]},
        "$or": [{"player1": user_id}, {"player2": user_id}]
    })
    if existing_lobby:
        await callback_query.answer("You are already in an active game or lobby!", show_alert=True)
        return

    # Check opponent balance
    bet = game["bet"]
    balance = await get_balance(user_id)
    if balance < bet:
        await callback_query.answer(f"Insufficient coins! You need {bet:,} coins.", show_alert=True)
        return

    # Deduct opponent balance
    await update_balance(user_id, -bet)

    # Random symbol allocation
    symbol_assignment = random.choice([
        (game["player1"], user_id), # Player 1 is X, Player 2 is O
        (user_id, game["player1"])  # Player 2 is X, Player 1 is O
    ])
    
    symbol_x = symbol_assignment[0]
    symbol_o = symbol_assignment[1]
    
    # Randomly select first turn
    first_turn = random.choice([game["player1"], user_id])

    # Update database
    await ox_games.update_one(
        {"game_id": game_id},
        {
            "$set": {
                "player2": user_id,
                "player2_name": first_name,
                "symbol_x": symbol_x,
                "symbol_o": symbol_o,
                "turn": first_turn,
                "status": "playing",
                "last_move_at": time.time()
            }
        }
    )

    game = await ox_games.find_one({"game_id": game_id})

    # Visual symbols
    player1_symbol = "❌" if game["symbol_x"] == game["player1"] else "⭕"
    player2_symbol = "❌" if game["symbol_x"] == game["player2"] else "⭕"
    
    turn_name = game["player1_name"] if game["turn"] == game["player1"] else game["player2_name"]
    turn_symbol = "❌" if game["symbol_x"] == game["turn"] else "⭕"

    caption_text = (
        "🎮 <b>Tic Tac Toe Game</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{player1_symbol} {game['player1_name']}\n"
        f"{player2_symbol} {game['player2_name']}\n\n"
        f"<b>Prize Pool:</b> <code>{game['prize_pool']:,}</code> Coins\n"
        f"<b>Turn:</b> {turn_name} ({turn_symbol})\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )

    await callback_query.message.edit_text(
        text=caption_text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=make_board_keyboard(game_id, game["board"])
    )
    await callback_query.answer("Match started! Let's play!")


@app.on_callback_query(filters.regex(r"^cancel_ox_(\w+)"))
async def cancel_ox_callback(client, callback_query):
    user_id = callback_query.from_user.id
    game_id = callback_query.data.split("_")[2]

    game = await ox_games.find_one({"game_id": game_id})
    if not game:
        await callback_query.answer("Game not found!", show_alert=True)
        return

    if game["status"] != "lobby":
        await callback_query.answer("This match cannot be cancelled anymore!", show_alert=True)
        return

    if game["player1"] != user_id:
        await callback_query.answer("Only the host can cancel this match!", show_alert=True)
        return

    # Update database
    await ox_games.update_one(
        {"game_id": game_id},
        {"$set": {"status": "cancelled"}}
    )

    # Refund host
    await update_balance(user_id, game["bet"])

    await callback_query.message.edit_text(
        f"❌ **Match Cancelled**\nNo opponent found. Host {game['player1_name']} refunded."
    )
    await callback_query.answer("Match cancelled. Refunded host.")


@app.on_callback_query(filters.regex(r"^ox_play_(\w+)_(\d+)_(\d+)"))
async def play_ox_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split("_")
    game_id = data[2]
    row = int(data[3])
    col = int(data[4])

    game = await ox_games.find_one({"game_id": game_id})
    if not game:
        await callback_query.answer("Game not found!", show_alert=True)
        return

    if game["status"] != "playing":
        await callback_query.answer("This game has ended!", show_alert=True)
        return

    # Validate active player participation
    if user_id != game["player1"] and user_id != game["player2"]:
        await callback_query.answer("This game is not for you!", show_alert=True)
        return

    # Validate turn sequence
    if user_id != game["turn"]:
        await callback_query.answer("It's not your turn!", show_alert=True)
        return

    # Validate cell occupancy
    board = game["board"]
    if board[row][col] != "":
        await callback_query.answer("This cell is already occupied!", show_alert=True)
        return

    # Play symbol (X or O)
    player_symbol = "X" if game["symbol_x"] == user_id else "O"
    board[row][col] = player_symbol

    # Check for winner / draw
    winner_symbol = check_winner(board)
    is_draw = False
    winner_id = None
    loser_id = None

    if winner_symbol:
        winner_id = game["symbol_x"] if winner_symbol == "X" else game["symbol_o"]
        loser_id = game["player2"] if winner_id == game["player1"] else game["player1"]
        status = "ended"
    elif is_board_full(board):
        is_draw = True
        status = "ended"
    else:
        status = "playing"

    # Toggle active turn
    next_turn = game["player2"] if game["turn"] == game["player1"] else game["player1"]

    if status == "ended":
        await ox_games.update_one(
            {"game_id": game_id},
            {
                "$set": {
                    "board": board,
                    "status": "ended",
                    "winner": winner_id,
                    "last_move_at": time.time()
                }
            }
        )
        
        if is_draw:
            # Refund both players
            await update_balance(game["player1"], game["bet"])
            await update_balance(game["player2"], game["bet"])
            
            # Record draws
            await record_game_draw(game["player1"], game["player2"], game["player1_name"], game["player2_name"])

            draw_text = (
                "🤝 <b>Match Draw!</b>\n\n"
                f"{game['bet']:,} Coins refunded to {game['player1_name']}\n"
                f"{game['bet']:,} Coins refunded to {game['player2_name']}"
            )
            await callback_query.message.edit_text(
                text=draw_text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=make_board_keyboard(game_id, board)
            )
            await callback_query.answer("Match Draw!")
        else:
            # Payout winner
            await update_balance(winner_id, game["prize_pool"])
            
            winner_name = game["player1_name"] if winner_id == game["player1"] else game["player2_name"]
            loser_name = game["player2_name"] if winner_id == game["player1"] else game["player1_name"]

            # Record stats
            await record_game_result(winner_id, loser_id, winner_name, loser_name)

            win_text = (
                f"🏆 <b>{winner_name} Won!</b>\n\n"
                f"Prize: <code>{game['prize_pool']:,}</code> Coins"
            )
            await callback_query.message.edit_text(
                text=win_text,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=make_board_keyboard(game_id, board)
            )
            await callback_query.answer(f"{winner_name} won!")
            
    else:
        # Continue game
        await ox_games.update_one(
            {"game_id": game_id},
            {
                "$set": {
                    "board": board,
                    "turn": next_turn,
                    "last_move_at": time.time()
                }
            }
        )
        
        player1_symbol = "❌" if game["symbol_x"] == game["player1"] else "⭕"
        player2_symbol = "❌" if game["symbol_x"] == game["player2"] else "⭕"
        
        next_turn_name = game["player1_name"] if next_turn == game["player1"] else game["player2_name"]
        next_turn_symbol = "❌" if game["symbol_x"] == next_turn else "⭕"

        caption_text = (
            "🎮 <b>Tic Tac Toe Game</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"{player1_symbol} {game['player1_name']}\n"
            f"{player2_symbol} {game['player2_name']}\n\n"
            f"<b>Prize Pool:</b> <code>{game['prize_pool']:,}</code> Coins\n"
            f"<b>Turn:</b> {next_turn_name} ({next_turn_symbol})\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )

        await callback_query.message.edit_text(
            text=caption_text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=make_board_keyboard(game_id, board)
        )
        await callback_query.answer()


# ── BACKGROUND MONITORING LOOP ──────────────────────────────────────────

async def ox_timeout_loop():
    while True:
        try:
            await asyncio.sleep(10)
            current_time = time.time()
            
            # 1. Cancel lobbies older than 5 minutes (300 seconds)
            expired_lobbies = ox_games.find({
                "status": "lobby",
                "created_at": {"$lt": current_time - 300}
            })
            
            async for lobby in expired_lobbies:
                # Cancel state and refund coins
                await ox_games.update_one(
                    {"game_id": lobby["game_id"]},
                    {"$set": {"status": "cancelled"}}
                )
                await update_balance(lobby["player1"], lobby["bet"])
                
                try:
                    await app.edit_message_text(
                        chat_id=lobby["chat_id"],
                        message_id=lobby["message_id"],
                        text=f"❌ **Match Cancelled**\nNo opponent found. Host {lobby['player1_name']} refunded."
                    )
                except Exception:
                    pass

            # 2. End games where player has been AFK for > 2 minutes (120 seconds)
            afk_games = ox_games.find({
                "status": "playing",
                "last_move_at": {"$lt": current_time - 120}
            })
            
            async for active_game in afk_games:
                afk_player_id = active_game["turn"]
                winner_id = active_game["player2"] if afk_player_id == active_game["player1"] else active_game["player1"]
                
                # End state
                await ox_games.update_one(
                    {"game_id": active_game["game_id"]},
                    {
                        "$set": {
                            "status": "ended",
                            "winner": winner_id
                        }
                    }
                )
                
                # Payout winner
                await update_balance(winner_id, active_game["prize_pool"])
                
                afk_player_name = active_game["player1_name"] if afk_player_id == active_game["player1"] else active_game["player2_name"]
                winner_name = active_game["player2_name"] if afk_player_id == active_game["player1"] else active_game["player1_name"]
                
                # Record stats
                await record_game_result(winner_id, afk_player_id, winner_name, afk_player_name)
                
                try:
                    afk_text = (
                        f"⏰ <b>{afk_player_name} AFK</b>\n\n"
                        f"🏆 <b>{winner_name} Won!</b>\n"
                        f"Prize: <code>{active_game['prize_pool']:,}</code> Coins"
                    )
                    await app.edit_message_text(
                        chat_id=active_game["chat_id"],
                        message_id=active_game["message_id"],
                        text=afk_text,
                        parse_mode=enums.ParseMode.HTML
                    )
                except Exception:
                    pass
                    
        except Exception as e:
            print(f"Error in ox_timeout_loop: {e}")

# Hook into python-telegram-bot application post_init to schedule task safely inside the event loop
original_post_init = getattr(application, 'post_init', None)

async def ox_post_init(app_ptb):
    if original_post_init:
        await original_post_init(app_ptb)
    asyncio.create_task(ox_timeout_loop())

application.post_init = ox_post_init
