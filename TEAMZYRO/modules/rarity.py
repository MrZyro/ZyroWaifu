# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

# TEAMZYRO/commands/rarity.py
from TEAMZYRO import app, collection
from pyrogram import filters, enums

@app.on_message(filters.command("rarity"))
async def rarity_count(client, message):
    try:
        # Fetch distinct rarities from the characters collection
        distinct_rarities = await collection.distinct('rarity')
        
        if not distinct_rarities:
            await message.reply_text("⚠️ No rarities found in the database.")
            return
        
        response_message = "✨ Character Count by Rarity ✨\n\n"
        total_count = 0  # total character counter
        
        # Loop through each rarity and count the number of characters
        for rarity in distinct_rarities:
            count = await collection.count_documents({'rarity': rarity})
            total_count += count
            response_message += f"◈ {rarity} — {count} character(s)\n"
        
        # Add total count at the end
        response_message += f"\n💠 Total Characters: {total_count}"
        
        await message.reply_text(response_message)
    
    except Exception as e:
        await message.reply_text(f"⚠️ Error: {str(e)}")
