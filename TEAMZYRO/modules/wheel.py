# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters, enums
from pyrogram.types import Message
from TEAMZYRO import app, user_collection, collection
import random
import asyncio

# Concurrency lock to prevent multiple spins
active_spins = set()

# Wheel sectors definitions
SECTORS = [
    ("❌ Bust (0.0x)", 0.0, 35),
    ("📉 Half Loss (0.5x)", 0.5, 20),
    ("⚖️ Push (1.0x)", 1.0, 15),
    ("📈 Win (1.5x)", 1.5, 15),
    ("🔥 Double (2.0x)", 2.0, 10),
    ("🚀 Jackpot (5.0x)", 5.0, 4),
    ("🌟 Waifu Drop", "waifu", 1)
]

def roll_wheel():
    sectors_list = []
    weights = []
    for sector in SECTORS:
        sectors_list.append(sector)
        weights.append(sector[2])
    return random.choices(sectors_list, weights=weights, k=1)[0]

async def get_drop_character():
    try:
        pipeline = [
            {
                '$match': {
                    'rarity': {'$in': ['🟡 Legendary', '🎐 Celestial', '🔮 Limited Edition', '💮 Special Edition']}, 
                    'img_url': {'$exists': True, '$ne': ''}, 
                    'id': {'$exists': True}, 
                    'name': {'$exists': True, '$ne': ''}, 
                    'anime': {'$exists': True, '$ne': ''}
                }
            },
            {'$sample': {'size': 1}}
        ]
        cursor = collection.aggregate(pipeline)
        characters = await cursor.to_list(length=None)
        if characters:
            return characters[0]
        return None
    except Exception as e:
        print(f"Error drawing drop character: {e}")
        return None

@app.on_message(filters.command(["wheel", "spin"]))
async def spin_wheel(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in active_spins:
        await message.reply_text(
            "🎡 <b>𝖶𝖧𝖤𝖤𝖫</b>\n\n"
            "<blockquote>⏳ Your previous spin is still processing! Please wait.</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    args = message.command
    if len(args) < 2:
        await message.reply_text(
            "🎡 <b>𝖶𝖧𝖤𝖤𝖫 𝖮𝖥 𝖥𝖮𝖱𝖳𝖴𝖭𝖤</b>\n\n"
            "<blockquote>🎮 <b>How to Play:</b>\n"
            "Use <code>/spin &lt;amount&gt;</code> to spin the lucky wheel!\n\n"
            "🎰 <b>Reels:</b>\n"
            "• Bust: 0.0x | Half Loss: 0.5x | Push: 1.0x\n"
            "• Win: 1.5x | Double: 2.0x | Jackpot: 5.0x\n"
            "• Waifu Drop: Random Legendary/Celestial waifu!\n\n"
            "⚠️ Min bet: 100 | Max bet: 50,000</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    try:
        amount = int(args[1])
        if amount < 100 or amount > 50000:
            await message.reply_text(
                "🎡 <b>𝖶𝖧𝖤𝖤𝖫</b>\n\n"
                "<blockquote>❌ Bet amount must be between 100 and 50,000 coins!</blockquote>",
                parse_mode=enums.ParseMode.HTML,
                quote=True
            )
            return
    except ValueError:
        await message.reply_text(
            "🎡 <b>𝖶𝖧𝖤𝖤𝖫</b>\n\n"
            "<blockquote>❌ Please enter a valid number for the bet amount!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    user_data = await user_collection.find_one({"id": user_id})
    if not user_data or user_data.get("balance", 0) < amount:
        await message.reply_text(
            "🎡 <b>𝖶𝖧𝖤𝖤𝖫</b>\n\n"
            "<blockquote>❌ Insufficient balance to place this bet!</blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        return

    active_spins.add(user_id)
    
    try:
        await user_collection.update_one({"id": user_id}, {"$inc": {"balance": -amount}})
        
        status_msg = await message.reply_text(
            f"🎡 <b>𝖫𝖴𝖢𝖪𝖸 𝖶𝖧𝖤𝖤𝖫 𝖲𝖯𝖨𝖭</b>\n\n"
            f"👤 <b>Player:</b> {message.from_user.mention}\n"
            f"<blockquote>💰 <b>Bet:</b> {amount} coins\n\n"
            f"🌀 <b>[ 🔴 🔵 🟡 🟢 ]</b>\n\n"
            f"<i>Spinning the wheel...</i></blockquote>",
            parse_mode=enums.ParseMode.HTML,
            quote=True
        )
        
        frames = [
            "🌀 <b>[ 🔵 🟡 🟢 🔴 ]</b>",
            "🌀 <b>[ 🟡 🟢 🔴 🔵 ]</b>",
            "🌀 <b>[ 🟢 🔴 🔵 🟡 ]</b>"
        ]
        
        for frame in frames:
            await asyncio.sleep(0.5)
            await status_msg.edit_text(
                f"🎡 <b>𝖫𝖴𝖢𝖪𝖸 𝖶𝖧𝖤𝖤𝖫 𝖲𝖯𝖨𝖭</b>\n\n"
                f"👤 <b>Player:</b> {message.from_user.mention}\n"
                f"<blockquote>💰 <b>Bet:</b> {amount} coins\n\n"
                f"{frame}\n\n"
                f"<i>Spinning the wheel...</i></blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            
        await asyncio.sleep(0.5)
        
        selected_sector = roll_wheel()
        sector_name, outcome, _ = selected_sector
        
        if outcome == "waifu":
            character = await get_drop_character()
            if character:
                await user_collection.update_one(
                    {"id": user_id},
                    {"$push": {"characters": character}},
                    upsert=True
                )
                
                caption_text = (
                    f"🎡 <b>𝖫𝖴𝖢𝖪𝖸 𝖶𝖧𝖤𝖤𝖫 𝖲𝖯𝖨𝖭</b>\n\n"
                    f"👤 <b>Player:</b> {message.from_user.mention}\n"
                    f"<blockquote>✨ <b>Landed on: {sector_name}!</b> ✨\n\n"
                    f"🎉 <b>𝖩𝖠𝖢𝖪𝖯𝖮𝖳!</b> You won a character drop!\n"
                    f"🌸 <b>Name:</b> {character['name']}\n"
                    f"⛩️ <b>Anime:</b> {character['anime']}\n"
                    f"🌈 <b>Rarity:</b> {character['rarity']}\n"
                    f"🆔 <b>ID:</b> {character['id']}</blockquote>"
                )
                
                await message.reply_photo(
                    photo=character['img_url'],
                    caption=caption_text,
                    parse_mode=enums.ParseMode.HTML
                )
                await status_msg.delete()
            else:
                outcome = 5.0
                sector_name = "🚀 Jackpot (5.0x) (Waifu fallback)"

        if isinstance(outcome, float) or isinstance(outcome, int):
            winnings = int(amount * outcome)
            
            updated_user = await user_collection.find_one_and_update(
                {"id": user_id},
                {"$inc": {"balance": winnings}},
                return_document=True
            )
            new_balance = updated_user.get("balance", 0)
            
            if winnings > amount:
                net_change = winnings - amount
                status_text = (
                    f"🎉 <b>𝖢𝖮𝖭𝖦𝖱𝖠𝖳𝖴𝖫𝖠𝖳𝖨𝖮𝖭𝖲!</b>\n"
                    f"💰 <b>Net Gain:</b> +{net_change} coins (Payout: {winnings})\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins"
                )
            elif winnings == amount:
                status_text = (
                    f"⚖️ <b>𝖯𝖴𝖲𝖧!</b>\n"
                    f"💰 Your bet has been fully refunded.\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins"
                )
            elif winnings > 0:
                net_loss = amount - winnings
                status_text = (
                    f"📉 <b>𝖧𝖠𝖫𝖥 𝖫𝖮𝖲𝖲!</b>\n"
                    f"💸 <b>Deducted:</b> -{net_loss} coins (Refunded: {winnings})\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins"
                )
            else:
                status_text = (
                    f"😭 <b>𝖡𝖴𝖲𝖳!</b> Better luck next time.\n"
                    f"💸 <b>Lost:</b> -{amount} coins\n"
                    f"💳 <b>New Balance:</b> {new_balance} coins"
                )
                
            await status_msg.edit_text(
                f"🎡 <b>𝖫𝖴𝖢𝖪𝖸 𝖶𝖧𝖤𝖤𝖫 𝖲𝖯𝖨𝖭</b>\n\n"
                f"👤 <b>Player:</b> {message.from_user.mention}\n"
                f"<blockquote>✨ <b>[ {sector_name} ]</b> ✨\n\n"
                f"{status_text}</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
            
    except Exception as e:
        print(f"Error in wheel spin: {e}")
        try:
            await user_collection.update_one({"id": user_id}, {"$inc": {"balance": amount}})
            await message.reply_text("⚠️ An error occurred during the spin. Refunded.", quote=True)
        except Exception:
            pass
    finally:
        active_spins.remove(user_id)
