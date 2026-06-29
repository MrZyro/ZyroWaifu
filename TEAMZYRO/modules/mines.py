# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import math
import random
import uuid
import re
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from TEAMZYRO import app, user_collection, collection

# Rarity Map
rarity_map = {
    1: "⚪️ Common",
    2: "🟣 Rare",
    3: "🟡 Legendary",      
    4: "🟢 Medium",  
    5: "💮 Special Edition", 
    6: "🔮 Limited Edition", 
    7: "💸 Premium Edition", 
    8: "🌤 Summer",
    9: "🎐 Celestial", 
    10: "❄️ Winter", 
    11: "💝 Valentine", 
    12: "🎃 Halloween", 
    13: "🎄 Christmas Special", 
    14: "🪐 Omniversal", 
    15: "🎭 Cosplay Master 🎭",
    16: "🧧 Events",
    17: "🍑 Echhi",
    18: "🎗️ AMV Edition",
}

# Game settings
GRID_SIZE = 4      # Upgraded to 4x4 Grid
MIN_BET = 500
MAX_BET = 100000
MIN_MINES = 3
MAX_MINES = 5
MAX_MINE_HITS = 1  # 1 mine hit is game over

# Math Combinations
def nCr(n, r):
    if r < 0 or r > n:
        return 0
    return math.comb(n, r)

# Multiplier Calculator based on Probability Theory
def get_multiplier(num_mines, safe_opened):
    if safe_opened <= 0:
        return 1.0
    total_cells = GRID_SIZE * GRID_SIZE
    total_ways = nCr(total_cells, safe_opened)
    safe_ways = nCr(total_cells - num_mines, safe_opened)
    if safe_ways == 0:
        return 0.0
    
    mult = total_ways / safe_ways
    # 95% Return to Player (RTP)
    return round(mult * 0.95, 2)

# Validate URL
def is_valid_url(url):
    if not url or not isinstance(url, str):
        return False
    return re.match(r'^https?://[^\s/$.?#].[^\s]*$', url) is not None

# Initialize grid and place mines
def create_game(num_mines):
    grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    total_cells = GRID_SIZE * GRID_SIZE
    mines_indices = random.sample(range(total_cells), num_mines)
    mines = [(idx // GRID_SIZE, idx % GRID_SIZE) for idx in mines_indices]
    return grid, mines

# Keyboard generator
def generate_keyboard(grid, game_id, player_id, safe_opened, mine_hits, num_mines):
    keyboard = []
    for i in range(GRID_SIZE):
        row = []
        for j in range(GRID_SIZE):
            val = grid[i][j]
            if val == 1:    # Opened safe
                row.append(InlineKeyboardButton("💎", callback_data=f"mine_{game_id}_{player_id}_{i}_{j}_opened"))
            elif val == 2:  # Hitted mine
                row.append(InlineKeyboardButton("💥", callback_data=f"mine_{game_id}_{player_id}_{i}_{j}_opened"))
            elif val == 3:  # Un-hit mine revealed
                row.append(InlineKeyboardButton("💣", callback_data=f"mine_{game_id}_{player_id}_{i}_{j}_opened"))
            elif val == 4:  # Unopened safe revealed
                row.append(InlineKeyboardButton("✨", callback_data=f"mine_{game_id}_{player_id}_{i}_{j}_opened"))
            else:           # Unopened
                row.append(InlineKeyboardButton("❓", callback_data=f"mine_{game_id}_{player_id}_{i}_{j}"))
        keyboard.append(row)
        
    game_over = mine_hits >= MAX_MINE_HITS
    if safe_opened > 0 and not game_over:
        mult = get_multiplier(num_mines, safe_opened)
        keyboard.append([InlineKeyboardButton(f"Claim Winnings ({mult}x)", callback_data=f"claim_{game_id}_{player_id}_{safe_opened}")])
    return InlineKeyboardMarkup(keyboard)

# Retrieve random character based on progression
async def get_random_character(user_id, safe_opened):
    try:
        user_data = await user_collection.find_one({'id': user_id}, {'filter_rarity': 1})
        filter_rarity = user_data.get('filter_rarity') if user_data else None

        if filter_rarity:
            if isinstance(filter_rarity, int):
                rarities = [rarity_map.get(filter_rarity)]
            else:
                rarities = [filter_rarity]
            rarities = [r for r in rarities if r is not None]
        else:
            if safe_opened < 6:
                rarities = ['⚪️ Common', '🟣 Rare', '🟢 Medium', '🟡 Legendary']
            else:
                rarities = ['💮 Special Edition', '🔮 Limited Edition', '💸 Premium Edition', '🎐 Celestial',]

        if not rarities:
            return None

        pipeline = [
            {'$match': {'rarity': {'$in': rarities}, 'img_url': {'$exists': True, '$ne': ''}, 'id': {'$exists': True}, 'name': {'$exists': True, '$ne': ''}, 'anime': {'$exists': True, '$ne': ''}}},
            {'$sample': {'size': 1}}
        ]
        
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=1)
        
        if characters and is_valid_url(characters[0].get('img_url')):
            return characters[0]
        return None
    except Exception as e:
        print(f"Error retrieving character: {e}")
        return None

# Award rewards
async def award_rewards(user_id, safe_opened, bet, num_mines):
    user_data = await user_collection.find_one({'id': user_id})
    if not user_data:
        user_data = {'id': user_id, 'username': '', 'first_name': '', 'balance': 0, 'tokens': 0, 'characters': []}

    mult = get_multiplier(num_mines, safe_opened)
    winnings = int(bet * mult)
    user_data['balance'] = user_data.get('balance', 0) + winnings

    character = None
    if safe_opened >= 4:
        drop_chance = min(80, (safe_opened * num_mines * 4))
        if random.randint(1, 100) <= drop_chance:
            character = await get_random_character(user_id, safe_opened)
            if character:
                user_data.setdefault('characters', []).append(character)

    try:
        await user_collection.update_one(
            {'id': user_id},
            {'$set': {'balance': user_data.get('balance', 0), 'characters': user_data.get('characters', [])}},
            upsert=True
        )
    except Exception as e:
        print(f"Error updating user_collection: {e}")
        return user_data, None, 0

    return user_data, character, winnings

# In-memory game state and locks
game_state = {}
processing_locks = set()

# Start mines command
@app.on_message(filters.command("mines"))
async def start_mines(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Defaults
    bet = 1000
    num_mines = 3
    
    args = message.command
    if len(args) > 1:
        try:
            bet = int(args[1])
        except ValueError:
            await message.reply_text("❌ Bet amount must be a positive integer!")
            return
            
    if len(args) > 2:
        try:
            num_mines = int(args[2])
        except ValueError:
            await message.reply_text("❌ Mine count must be a positive integer!")
            return

    if bet < MIN_BET or bet > MAX_BET:
        await message.reply_text(f"❌ Bet amount must be between {MIN_BET:,} and {MAX_BET:,} coins!")
        return
        
    if num_mines < MIN_MINES or num_mines > MAX_MINES:
        await message.reply_text(f"❌ Mine count must be between {MIN_MINES} and {MAX_MINES}!")
        return

    user_data = await user_collection.find_one({'id': user_id}, {'balance': 1})
    if not user_data or user_data.get('balance', 0) < bet:
        await message.reply_text(f"❌ You do not have enough coins to bet {bet:,}! Check `/balance`.")
        return

    try:
        await user_collection.update_one({'id': user_id}, {'$inc': {'balance': -bet}})
    except Exception as e:
        print(f"Error deducting balance: {e}")
        await message.reply_text("❌ Error starting game. Try again later.")
        return
    
    game_id = str(uuid.uuid4())
    player_id = str(user_id)
    grid, mines = create_game(num_mines)
    
    game_state[user_id] = {
        'grid': grid, 'mines': mines, 'game_id': game_id, 'player_id': player_id,
        'safe_opened': 0, 'mine_hits': 0, 'bet': bet, 'num_mines': num_mines
    }
    
    caption_text = (
        "🎮 <b>Minesweeper Casino</b> 🎮\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Player:</b> {message.from_user.first_name}\n"
        f"💰 <b>Bet Amount:</b> <code>{bet:,}</code> coins\n"
        f"💣 <b>Mines Hidden:</b> <code>{num_mines}</code>\n\n"
        "💎 Sweep the 4x4 grid and open safe cells to increase your multiplier!\n"
        "⚠️ Watch out for hidden mines!"
    )
    
    await message.reply_photo(
        photo="https://files.catbox.moe/szew66.png",
        caption=caption_text,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=generate_keyboard(grid, game_id, player_id, 0, 0, num_mines)
    )

# Handle clicks on the grid
@app.on_callback_query(filters.regex(r'mine_(\S+)_(\d+)_(\d+)_(\d+)(?:_opened)?'))
async def handle_mine_click(client: Client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data.split('_')
    game_id, player_id, x, y = data[1], data[2], int(data[3]), int(data[4])
    
    if str(user_id) != player_id:
        await callback_query.answer("This is not your game!", show_alert=True)
        return
    
    if user_id not in game_state or game_state[user_id]['game_id'] != game_id:
        await callback_query.answer("Game expired or invalid!", show_alert=True)
        return
    
    state = game_state[user_id]
    grid, mines, safe_opened, mine_hits = state['grid'], state['mines'], state['safe_opened'], state['mine_hits']
    bet, num_mines = state['bet'], state['num_mines']
    
    if grid[x][y] in [1, 2]:
        await callback_query.answer("This cell has already been revealed!", show_alert=True)
        return
    
    if (x, y) in mines:
        state['mine_hits'] += 1
        grid[x][y] = 2
        
        # Game Over - Reveal board
        for r_x in range(GRID_SIZE):
            for r_y in range(GRID_SIZE):
                if (r_x, r_y) in mines:
                    if grid[r_x][r_y] != 2:
                        grid[r_x][r_y] = 3
                else:
                    if grid[r_x][r_y] != 1:
                        grid[r_x][r_y] = 4
        
        caption = (
            "💥 <b>BOOM! Game Over!</b> 💥\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"You hit a mine and lost your bet of <b>{bet:,} coins</b>!\n\n"
            "💣 = Mine Locations | ✨ = Safe Boxes"
        )
        await callback_query.message.edit_text(
            caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=generate_keyboard(grid, game_id, player_id, safe_opened, state['mine_hits'], num_mines)
        )
        del game_state[user_id]
        return
    else:
        grid[x][y] = 1
        state['safe_opened'] += 1
        safe_opened = state['safe_opened']
        
        # Check if all safe cells opened
        total_safes = (GRID_SIZE * GRID_SIZE) - num_mines
        if safe_opened >= total_safes:
            # Automatic claim as board is fully swept!
            del game_state[user_id]
            user_data, character, winnings = await award_rewards(user_id, safe_opened, bet, num_mines)
            
            caption = (
                "🎉 <b>PERFECT BOARD CLEAR!</b> 🎉\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"You successfully cleared all safe cells!\n"
                f"📈 <b>Multiplier:</b> {get_multiplier(num_mines, safe_opened)}x\n"
                f"💰 <b>Winnings:</b> <code>{winnings:,}</code> coins!"
            )
            if character:
                caption += (
                    f"\n\n🎁 <b>Bonus Character Reward:</b>\n"
                    f"🌸 <b>Name:</b> {character['name']}\n"
                    f"⛩️ <b>Anime:</b> {character['anime']}\n"
                    f"🌈 <b>Rarity:</b> {character['rarity']}"
                )
                if character.get('img_url'):
                    await callback_query.message.reply_photo(photo=character['img_url'], caption=caption, parse_mode=enums.ParseMode.HTML)
                    await callback_query.message.delete()
                    return
            
            await callback_query.message.edit_text(caption, parse_mode=enums.ParseMode.HTML)
            return
        
        mult = get_multiplier(num_mines, safe_opened)
        caption = (
            "💎 <b>Safe Cell Opened!</b> 💎\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 <b>Diamonds Found:</b> {safe_opened} / {total_safes}\n"
            f"📈 <b>Multiplier:</b> {mult}x\n"
            f"💵 <b>Current Valuation:</b> <code>{int(bet * mult):,}</code> coins"
        )
        await callback_query.message.edit_text(
            caption,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=generate_keyboard(grid, game_id, player_id, safe_opened, state['mine_hits'], num_mines)
        )

# Claim winnings
@app.on_callback_query(filters.regex(r'claim_(\S+)_(\d+)_(\d+)'))
async def handle_claim(client: Client, callback_query):
    user_id = callback_query.from_user.id
    
    if user_id in processing_locks:
        await callback_query.answer("Your request is being processed. Please wait.", show_alert=True)
        return
    
    processing_locks.add(user_id)
    try:
        data = callback_query.data.split('_')
        game_id, player_id, safe_opened = data[1], data[2], int(data[3])
        
        if str(user_id) != player_id:
            await callback_query.answer("This is not your game!", show_alert=True)
            return
        
        if user_id not in game_state or game_state[user_id]['game_id'] != game_id:
            await callback_query.answer("Game expired or invalid!", show_alert=True)
            return
        
        state = game_state[user_id]
        bet = state['bet']
        num_mines = state['num_mines']
        
        del game_state[user_id]

        # Award rewards
        user_data, character, winnings = await award_rewards(user_id, safe_opened, bet, num_mines)
        
        mult = get_multiplier(num_mines, safe_opened)
        caption_text = (
            "💰 <b>Winnings Claimed!</b> 💰\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>Multiplier:</b> {mult}x\n"
            f"💰 <b>Cashout:</b> <code>{winnings:,}</code> coins!"
        )
        
        if character:
            caption_text += (
                f"\n\n🎁 <b>Bonus Character Reward:</b>\n"
                f"🌸 <b>Name:</b> {character['name']}\n"
                f"⛩️ <b>Anime:</b> {character['anime']}\n"
                f"🌈 <b>Rarity:</b> {character['rarity']}\n"
                f"🆔 <b>ID:</b> {character['id']}"
            )
            if character.get('img_url'):
                await callback_query.message.reply_photo(
                    photo=character['img_url'],
                    caption=caption_text,
                    parse_mode=enums.ParseMode.HTML
                )
                await callback_query.message.delete()
                return

        await callback_query.message.edit_text(caption_text, parse_mode=enums.ParseMode.HTML)
    
    finally:
        if user_id in processing_locks:
            processing_locks.remove(user_id)
