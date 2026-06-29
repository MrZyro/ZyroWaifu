# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import os
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from TEAMZYRO import app, user_collection, db
from TEAMZYRO.unit.zyro_rarity import rarity_map

def get_default_avatar():
    # Antique grey/brown silhouette shape as fallback
    avatar = Image.new("RGB", (550, 400), (220, 205, 175))
    draw = ImageDraw.Draw(avatar)
    
    # Silhouette face and body outline
    draw.ellipse([195, 50, 355, 230], fill=(130, 110, 90))
    draw.rectangle([135, 230, 415, 400], fill=(110, 90, 70))
    return avatar

async def fetch_and_resize_profile_photo(client, user_id):
    photos = []
    try:
        async for photo in client.get_chat_photos(user_id, limit=1):
            photos.append(photo)
    except Exception:
        pass

    if not photos:
        return None

    try:
        temp_file_path = await client.download_media(photos[0].file_id)
        with open(temp_file_path, "rb") as file:
            file_content = file.read()
        
        os.remove(temp_file_path)
        return io.BytesIO(file_content)
    except Exception as e:
        print(f"Error downloading profile photo: {e}")
        return None

def draw_wanted_poster(name, coins, profile_photo_stream=None):
    width = 700
    height = 1000
    bg_color = (235, 218, 183)  # #EBD8B7
    dark_brown = (63, 38, 21)    # #3F2615
    
    # Base Image
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Outer double borders
    draw.rectangle([0, 0, width-1, height-1], outline=dark_brown, width=22)
    draw.rectangle([35, 35, width-36, height-36], outline=dark_brown, width=3)
    
    # Load Font helper (uses PlayfairDisplay-Bold.ttf copied from Windows system font)
    font_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "PlayfairDisplay-Bold.ttf")
    
    def get_font(size):
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
        return ImageFont.load_default()

    # Draw Title "WANTED"
    wanted_font = get_font(105)
    wanted_text = "WANTED"
    w_width = draw.textlength(wanted_text, font=wanted_font)
    draw.text(((width - w_width)/2, 60), wanted_text, fill=dark_brown, font=wanted_font)
    
    # Picture Box Frame
    photo_x1, photo_y1 = 65, 195
    photo_x2, photo_y2 = 635, 615
    draw.rectangle([photo_x1, photo_y1, photo_x2, photo_y2], outline=dark_brown, width=6)
    
    # Draw photo or fallback
    profile_w, profile_h = 550, 400
    if profile_photo_stream:
        try:
            profile_photo_stream.seek(0)
            with Image.open(profile_photo_stream) as p_img:
                p_img_resized = ImageOps.fit(p_img, (profile_w, profile_h), Image.Resampling.LANCZOS)
                img.paste(p_img_resized, (75, 205))
        except Exception:
            img.paste(get_default_avatar(), (75, 205))
    else:
        img.paste(get_default_avatar(), (75, 205))
        
    # "DEAD OR ALIVE"
    doa_font = get_font(42)
    doa_text = "DEAD OR ALIVE"
    doa_w = draw.textlength(doa_text, font=doa_font)
    draw.text(((width - doa_w)/2, 650), doa_text, fill=dark_brown, font=doa_font)
    
    # Ribbon style lines
    line_y = 675
    draw.line([80, line_y, (width - doa_w)/2 - 20, line_y], fill=dark_brown, width=3)
    draw.line([(width + doa_w)/2 + 20, line_y, width - 80, line_y], fill=dark_brown, width=3)
    
    # User Name (e.g. MONKEY D. LUFFY)
    name = name.upper()
    name_font_size = 65
    name_font = get_font(name_font_size)
    name_w = draw.textlength(name, font=name_font)
    
    # Scale name down if it's too long
    while name_w > 540 and name_font_size > 30:
        name_font_size -= 3
        name_font = get_font(name_font_size)
        name_w = draw.textlength(name, font=name_font)
        
    draw.text(((width - name_w)/2, 720), name, fill=dark_brown, font=name_font)
    
    # Bounty Amount (e.g. ฿ 3,000,000,000-)
    bounty_val_text = f"{coins:,.0f}-"
    bounty_font_size = 55
    bounty_font = get_font(bounty_font_size)
    
    # Programmatic ฿ berry symbol drawing using B and two vertical slashes
    sym_w = draw.textlength("B", font=bounty_font)
    val_w = draw.textlength(bounty_val_text, font=bounty_font)
    total_w = sym_w + 10 + val_w
    
    while total_w > 540 and bounty_font_size > 25:
        bounty_font_size -= 2
        bounty_font = get_font(bounty_font_size)
        val_w = draw.textlength(bounty_val_text, font=bounty_font)
        sym_w = draw.textlength("B", font=bounty_font)
        total_w = sym_w + 10 + val_w
        
    start_x = (width - total_w) / 2
    y_pos = 805
    
    # 1. Draw letter B
    draw.text((start_x, y_pos), "B", fill=dark_brown, font=bounty_font)
    
    # 2. Add strike-through lines to B to form ฿
    bbox = draw.textbbox((start_x, y_pos), "B", font=bounty_font)
    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) / 2
    h = y2 - y1
    line_thickness = max(2, int(h * 0.05))
    offset = max(3, int(h * 0.08))
    draw.line([cx - offset, y1 - 4, cx - offset, y2 + 4], fill=dark_brown, width=line_thickness)
    draw.line([cx + offset, y1 - 4, cx + offset, y2 + 4], fill=dark_brown, width=line_thickness)
    
    # 3. Draw value text
    draw.text((start_x + sym_w + 10, y_pos), bounty_val_text, fill=dark_brown, font=bounty_font)
    
    # Tiny One Piece disclaimer
    disc_font = ImageFont.load_default()
    disc_text = "KONO SAKUHIN WA FICTION DETHUNODE JITSUZAISURU JINBUTSU DANTAI\nSONOTA NO SOSHIKE TO BOITSU NO MESHOU GA GEKICHU NI TOUYOU\nSHITATOSHITEMO JITSUZAI NO MONOTOWA ISSAI MUKANKEIDETH"
    draw.text((65, 890), disc_text, fill=dark_brown, font=disc_font)
    
    # MARINE
    marine_font = get_font(48)
    marine_text = "MARINE"
    marine_w = draw.textlength(marine_text, font=marine_font)
    draw.text((width - 65 - marine_w, 885), marine_text, fill=dark_brown, font=marine_font)
    
    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='PNG')
    img_byte_array.seek(0)
    return img_byte_array

@app.on_message(filters.command("bounty"))
async def mybounty_handler(client: Client, message: Message):
    # Parse target user
    target_user = None
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        args = message.command[1]
        if args.isdigit():
            try:
                target_user = await client.get_users(int(args))
            except Exception:
                pass
        else:
            try:
                target_user = await client.get_users(args.replace("@", ""))
            except Exception:
                pass
    
    if not target_user:
        target_user = message.from_user
        
    user_id = target_user.id
    first_name = target_user.first_name or "Unknown"
    
    loading_msg = await message.reply_text("⏳ Generating bounty poster...")
    
    user = await user_collection.find_one({'id': user_id})
    total_bounty = user.get('balance', 0) if user else 0
    characters = user.get('characters', []) if user else []
    total_chars = len(characters)
    
    # Compute rarity counts
    rarity_counts = {}
    rarity_name_to_id = {v: k for k, v in rarity_map.items()}
    
    for character in characters:
        rarity_name = character.get('rarity')
        if rarity_name:
            rarity_counts[rarity_name] = rarity_counts.get(rarity_name, 0) + 1
            
    # Format rarity breakdown text
    if rarity_counts:
        rarity_breakdown = "\n".join(f"{rarity}: {count}" for rarity, count in rarity_counts.items())
        top_rarity_name = max(rarity_counts.items(), key=lambda x: x[1])[0]
    else:
        rarity_breakdown = "No characters collected yet."
        top_rarity_name = "None"
        
    # Download profile photo
    profile_photo_stream = await fetch_and_resize_profile_photo(client, user_id)
    
    # Draw wanted poster
    try:
        poster_img = draw_wanted_poster(first_name, total_bounty, profile_photo_stream)
    except Exception as e:
        try:
            await loading_msg.delete()
        except Exception:
            pass
        await message.reply_text(f"❌ Failed to generate poster: {e}")
        return
        
    try:
        await loading_msg.delete()
    except Exception:
        pass
    
    caption = (
        f"🏴‍☠️ **{first_name}'s Bounty Report**\n\n"
        f"🏆 **Bounty Status:** Wanted\n"
        f"🎯 **Total Characters:** `{total_chars}`\n"
        f"💰 **Total Bounty:** `{total_bounty:,}` coins\n"
        f"⭐ **Top Rarity:** `{top_rarity_name}`\n\n"
        f"**Rarity Breakdown:**\n"
        f"{rarity_breakdown}"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support Group", url="https://t.me/oneforall_support")]
    ])
    
    await message.reply_photo(
        photo=poster_img,
        caption=caption,
        reply_markup=buttons,
        quote=True
    )
