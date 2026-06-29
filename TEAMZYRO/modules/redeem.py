# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import random
import string
from pymongo import ReturnDocument
from pyrogram import Client, filters
from pyrogram import enums
from TEAMZYRO import ZYRO as app
from TEAMZYRO import collection, user_collection, db, require_power

redeem_collection = db["redeem_codes"]  # Collection for redeem codes

# Command to generate a redeem code
@app.on_message(filters.command("cgen"))
@require_power("VIP")
async def generate_redeem_code(client, message):
    args = message.command
    if len(args) < 3:
        await message.reply_text("Usage: `/cgen <character_id> <redeem_limit>`", parse_mode=enums.ParseMode.MARKDOWN)
        return

    character_id = args[1]
    try:
        redeem_limit = int(args[2])
    except ValueError:
        await message.reply_text("Invalid redeem limit. It must be a number.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    # Check if character exists
    character = await collection.find_one({'id': character_id})
    if not character:
        await message.reply_text("❌ Character not found.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    # Generate a unique redeem code
    redeem_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Save redeem code in the database
    await redeem_collection.insert_one({
        "code": redeem_code,
        "character_id": character_id,
        "character_name": character["name"],
        "redeem_limit": redeem_limit,
        "redeemed_by": []
    })

    # Formatting message properly
    char_info = (
        f"🎭 *Character:* `{character['name']}`\n"
        f"📺 *Anime:* `{character.get('anime', 'Unknown')}`\n"
        f"🌟 *Rarity:* `{character.get('rarity', 'Unknown')}`\n"
        f"🖼 *Image:* [Click Here]({character.get('img_url', '#' )})\n\n"
        f"🔢 *Redeem Limit:* `{redeem_limit}`\n"
        f"🎟 *Redeem Code:* `{redeem_code}`"
    )

    await message.reply_text(f"✅ *Redeem code generated!*\n\n{char_info}", 
                             parse_mode=enums.ParseMode.MARKDOWN, 
                             disable_web_page_preview=True)


# Command to redeem a code
lock = {}  # Dictionary to prevent multiple redemptions at once

# Command to redeem a code
@app.on_message(filters.command("redeem"))
async def redeem_character(client, message):
    args = message.command
    if len(args) < 2:
        await message.reply_text("Usage: `/redeem <code>`", parse_mode=enums.ParseMode.MARKDOWN)
        return

    redeem_code = args[1]
    user_id = message.from_user.id

    if redeem_code == "1APRGIFT":
        await message.reply_text("🤣 Aap pagal ban chuke ho! Happy April Fool! 🎉", parse_mode=enums.ParseMode.MARKDOWN)
        return

    # Normal redeem process agar special code nahi hai
    redeem_data = await redeem_collection.find_one({"code": redeem_code})
    if not redeem_data:
        await message.reply_text("❌ Invalid or expired redeem code.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    if user_id in redeem_data["redeemed_by"]:
        await message.reply_text("❌ You have already redeemed this code.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    if len(redeem_data["redeemed_by"]) >= redeem_data["redeem_limit"]:
        await message.reply_text("❌ This redeem code has reached its limit.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    character = await collection.find_one({'id': redeem_data["character_id"]})
    if not character:
        await message.reply_text("❌ Character not found.", parse_mode=enums.ParseMode.MARKDOWN)
        return

    await user_collection.update_one(
        {'id': user_id},
        {'$push': {'characters': character}},
        upsert=True
    )

    await redeem_collection.update_one(
        {"code": redeem_code},
        {"$push": {"redeemed_by": user_id}}
    )

    char_info = (
        f"🎭 *Character:* `{character['name']}`\n"
        f"📺 *Anime:* `{character.get('anime', 'Unknown')}`\n"
        f"🌟 *Rarity:* `{character.get('rarity', 'Unknown')}`\n"
        f"🖼 *Image:* [Click Here]({character.get('img_url', '#' )})\n\n"
        f"🎉 *You have successfully redeemed this character!*"
    )

    await message.reply_text(char_info, parse_mode=enums.ParseMode.MARKDOWN, disable_web_page_preview=True)

