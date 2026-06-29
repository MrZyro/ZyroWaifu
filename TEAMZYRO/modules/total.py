# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from TEAMZYRO.unit.zyro_inline import get_all_characters
from TEAMZYRO import app 

@app.on_message(filters.command("total"))
async def total_characters(client: Client, message: Message):
    try:
        all_characters = await get_all_characters()
        unique_characters = len({char['id']: char for char in all_characters if 'id' in char})
        await message.reply_text(
            f"📊 <b>Total Characters in Bot:</b> <code>{unique_characters}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"❌ Error getting character count: {str(e)}")
