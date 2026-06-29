# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters
from pyrogram.types import Message
import html
from TEAMZYRO import *
import asyncio
from pyrogram import enums

async def get_user_stats(user_id):
    # Fetch user data
    user_data = await user_collection.find_one({'id': user_id}, {'balance': 1, 'first_name': 1, 'characters': 1})
    if not user_data:
        return None, "User data not found."
    
    balance = user_data.get('balance', 0)
    first_name = html.escape(user_data.get('first_name', 'Unknown'))
    characters = user_data.get('characters', [])
    
    # Calculate total characters in collection
    total_characters = await collection.count_documents({})
    
    # Calculate character count and collection progress
    character_count = len(characters)
    progress_percentage = (character_count / total_characters * 100) if total_characters > 0 else 0
    
    # Create progress bar
    progress_bar_length = 10
    filled_slots = int(progress_percentage / 100 * progress_bar_length)
    progress_bar = '█' * filled_slots + '□' * (progress_bar_length - filled_slots)
    
    # Fetch global rank
    cursor = user_collection.find({}, {"_id": 0, "id": 1, "characters": 1})
    all_users = await cursor.to_list(length=None)
    all_users.sort(key=lambda x: len(x.get('characters', [])), reverse=True)
    total_users = len(all_users)
    rank = next((i + 1 for i, user in enumerate(all_users) if user['id'] == user_id), total_users)
    
    # Count characters by rarity
    rarity_counts = {rarity: 0 for rarity in rarity_map.values()}
    for char in characters:
        rarity = char.get('rarity')
        if rarity in rarity_counts:
            rarity_counts[rarity] += 1
    
    return {
        'user_id': user_id,
        'first_name': first_name,
        'balance': balance,
        'character_count': character_count,
        'total_characters': total_characters,
        'progress_percentage': progress_percentage,
        'progress_bar': progress_bar,
        'rank': rank,
        'total_users': total_users,
        'rarity_counts': rarity_counts
    }, None

@app.on_message(filters.command("stats"))
async def stats_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Send initial "Processing..." message with the image
    processing_message = await message.reply_photo(
        photo=STATS_IMG[0],
        caption="Processing...",
        parse_mode=enums.ParseMode.HTML
    )
    
    # Small delay to simulate processing
    await asyncio.sleep(1)
    
    stats, error = await get_user_stats(user_id)
    
    if error:
        await processing_message.edit_caption(caption=error, parse_mode=enums.ParseMode.HTML)
        return
    
    # Build the stats caption
    stats_message = (
        f"❖ 【ＺＹＲＯ】{stats['first_name']} ɪɴғᴏʀᴍᴀᴛɪᴏɴ ❖\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⬤ ᴜsᴇʀ ɪᴅ ➥ {stats['user_id']}\n"
        f"⬤ ᴍᴇɴᴛɪᴏɴ ➥ {stats['first_name']}\n"
        f"⬤ ᴄᴏɪɴ ➥ {stats['balance']}\n"
        f"⬤ ᴄᴏʟʟᴇᴄᴛɪᴏɴ ➥ {stats['character_count']}/{stats['total_characters']} (total)\n"
        f"⬤ ᴘʀᴏɢʀᴇss ʙᴀʀ ➥ [{stats['progress_bar']} {stats['progress_percentage']:.2f}%]\n"
        f"⬤ ɢʟᴏʙᴀʟ ʀᴀɴᴋ ➥ {stats['rank']}/{stats['total_users']}\n"
        f"⬤ ʀᴀʀɪᴛʏ ᴄᴏᴜɴᴛ ➥\n"
    )
    
    # Add rarity counts
    for rarity, count in stats['rarity_counts'].items():
        emoji = rarity_map2.get(rarity, '❍')
        stats_message += f"  ❍ {rarity} ➥ {count}\n"
    
    stats_message += "━━━━━━━━━━━━━━━━━━━━━"
    
    # Edit the processing message with the final stats
    await processing_message.edit_caption(
        caption=stats_message,
        parse_mode=enums.ParseMode.HTML
    )
