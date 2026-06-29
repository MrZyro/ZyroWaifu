# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import os
import requests
from pyrogram import Client, filters
from pymongo import ReturnDocument
from gridfs import GridFS
from TEAMZYRO import application, DATABASE_ID, SUPPORT_CHAT, OWNER_ID, collection, user_collection, db, rarity_map, ZYRO, require_power, IMGBB_API_KEY

# Define the wrong format message and rarity map
WRONG_FORMAT_TEXT = """Wrong ❌ format...  eg. /upload reply to photo muzan-kibutsuji Demon-slayer 3

format:- /upload reply character-name anime-name rarity-number

use rarity number accordingly rarity Map

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
    19: "🌟 Luminous",
    20: "🌧 Rainy",
    22: "🍭 Winter event",
}
"""

async def find():
    cursor = collection.find().sort('id', 1)
    ids = []

    async for doc in cursor:
        if 'id' in doc:
            ids.append(int(doc['id']))

    # Check for gaps in the sequence
    ids.sort()
    for i in range(1, len(ids) + 2):  # Include one extra for the next ID if no gaps
        if i not in ids:
            return str(i).zfill(2)  # Return the missing ID

    return str(len(ids) + 1).zfill(2)  # If no gaps, return the next sequential ID


# Function to find the next available ID for a character
async def find_available_id():
    cursor = collection.find().sort('id', 1)
    ids = []

    async for doc in cursor:
        if 'id' in doc:
            ids.append(int(doc['id']))

    # Check for gaps in the sequence
    ids.sort()
    for i in range(1, len(ids) + 2):  # Include one extra for the next ID if no gaps
        if i not in ids:
            return str(i).zfill(2)  # Return the missing ID

    return str(len(ids) + 1).zfill(2)  # If no gaps, return the next sequential ID


def upload_to_catbox(file_path=None, file_url=None, expires=None, secret=None):
    url = "https://catbox.moe/user/api.php"
    with open(file_path, "rb") as file:
        response = requests.post(
            url,
            data={"reqtype": "fileupload"},
            files={"fileToUpload": file}
        )
        if response.status_code == 200 and response.text.startswith("https"):
            return response.text.strip()
        else:
            raise Exception(f"Error uploading to Catbox: {response.text}")


# IMGBB_API_KEY imported from TEAMZYRO

def upload_to_imgbb(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise Exception(f"Invalid file path: {file_path}")
    url = "https://api.imgbb.com/1/upload"
    with open(file_path, "rb") as f:
        response = requests.post(
            url,
            data={"key": IMGBB_API_KEY},
            files={"image": f}
        )
    if response.status_code == 200:
        data = response.json()
        return data["data"]["url"]
    else:
        raise Exception(f"HTTP Error: {response.status_code} | {response.text}")


server_collection = db["user_upload_servers"]

async def get_user_server(user_id: int) -> str:
    doc = await server_collection.find_one({"user_id": user_id})
    if doc:
        return doc.get("server", "imgbb")
    return "imgbb"

async def set_user_server(user_id: int, server: str):
    await server_collection.update_one(
        {"user_id": user_id},
        {"$set": {"server": server}},
        upsert=True
    )


@ZYRO.on_message(filters.command(["find"]))
@require_power("add")
async def ul(client, message):
    available_id = await find()
    await message.reply_text(
                f"new id {available_id}"
            )


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@ZYRO.on_message(filters.command("server"))
@require_power("add")
async def select_server(client, message):
    current_server = await get_user_server(message.from_user.id)
    buttons = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("ImgBB ✅" if current_server == "imgbb" else "ImgBB", callback_data="set_server_imgbb"),
            InlineKeyboardButton("Catbox ✅" if current_server == "catbox" else "Catbox", callback_data="set_server_catbox")
        ]]
    )
    await message.reply(f"Your current upload server is **{current_server.upper()}**.\nSelect upload server:", reply_markup=buttons)


@ZYRO.on_callback_query(filters.regex(r"^set_server_"))
@require_power("add")
async def server_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    if data == "set_server_imgbb":
        await set_user_server(user_id, "imgbb")
        buttons = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("ImgBB ✅", callback_data="set_server_imgbb"),
                InlineKeyboardButton("Catbox", callback_data="set_server_catbox")
            ]]
        )
        await callback_query.edit_message_text("Upload server set to ImgBB ✅", reply_markup=buttons)
        await callback_query.answer("Upload server set to ImgBB ✅", show_alert=True)
    elif data == "set_server_catbox":
        await set_user_server(user_id, "catbox")
        buttons = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("ImgBB", callback_data="set_server_imgbb"),
                InlineKeyboardButton("Catbox ✅", callback_data="set_server_catbox")
            ]]
        )
        await callback_query.edit_message_text("Upload server set to Catbox ✅", reply_markup=buttons)
        await callback_query.answer("Upload server set to Catbox ✅", show_alert=True)


import asyncio

upload_lock = asyncio.Lock()  # Lock for handling concurrent uploads

@ZYRO.on_message(filters.command(["gupload", "u", "upload"]))
@require_power("add")
async def ul_main(client, message):
    global upload_lock

    if upload_lock.locked():
        await message.reply_text("Another upload is in progress. Please wait until it is completed.")
        return

    async with upload_lock:  # Acquire lock
        reply = message.reply_to_message
        if reply and (reply.photo or reply.document or reply.video):
            args = message.text.split()
            if len(args) != 4:
                await client.send_message(chat_id=message.chat.id, text=WRONG_FORMAT_TEXT)
                return

            # Extract character details from the command arguments
            character_name = args[1].replace('-', ' ').title()
            anime = args[2].replace('-', ' ').title()
            rarity = int(args[3])

            # Validate rarity value
            if rarity not in rarity_map:
                await message.reply_text("Invalid rarity value. Please use a value between 1 and 16.")
                return

            rarity_text = rarity_map[rarity]
            available_id = await find_available_id()

            # Prepare character data
            character = {
                'name': character_name,
                'anime': anime,
                'rarity': rarity_text,
                'id': available_id
            }

            processing_message = await message.reply("<ᴘʀᴏᴄᴇꜱꜱɪɴɢ>....")
            path = await reply.download()
            try:
                # Upload image or video using user's selected server
                server = await get_user_server(message.from_user.id)
                
                # Check if it's a document/video and fallback to catbox if user has imgbb selected
                is_video = bool(reply.video)
                is_doc_non_image = False
                if reply.document:
                    mime = getattr(reply.document, "mime_type", "") or ""
                    if not mime.startswith("image/"):
                        is_doc_non_image = True

                if server == "imgbb" and not is_video and not is_doc_non_image:
                    try:
                        file_url = upload_to_imgbb(path)
                    except Exception as e:
                        # Fallback to catbox
                        file_url = upload_to_catbox(path)
                else:
                    file_url = upload_to_catbox(path)

                # Update character with the image or video URL
                if reply.photo or reply.document:
                    character['img_url'] = file_url
                elif reply.video:
                    character['vid_url'] = file_url
                    # Download and upload thumbnail
                    thumbnail_path = await client.download_media(reply.video.thumbs[0].file_id)
                    if server == "imgbb":
                        try:
                            thumbnail_url = upload_to_imgbb(thumbnail_path)
                        except Exception:
                            thumbnail_url = upload_to_catbox(thumbnail_path)
                    else:
                        thumbnail_url = upload_to_catbox(thumbnail_path)
                    character['thum_url'] = thumbnail_url
                    os.remove(thumbnail_path)  # Clean up the thumbnail file

                # Send character details to the channel
                if reply.photo or reply.document:
                    await client.send_photo(
                        chat_id=DATABASE_ID,
                        photo=file_url,
                        caption=(
                            f"Character Name: {character_name}\n"
                            f"Anime Name: {anime}\n"
                            f"Rarity: {rarity_text}\n"
                            f"ID: {available_id}\n"
                            f"Added by [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
                        ),
                    )
                elif reply.video:
                    await client.send_video(
                        chat_id=DATABASE_ID,
                        video=file_url,
                        caption=(
                            f"Character Name: {character_name}\n"
                            f"Anime Name: {anime}\n"
                            f"Rarity: {rarity_text}\n"
                            f"ID: {available_id}\n"
                            f"Added by [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n\n"
                        ),
                    )

                # Insert character into the database
                await collection.insert_one(character)
                await message.reply_text(
                    f"➲ ᴀᴅᴅᴇᴅ ʙʏ» [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n"
                    f"➥ Character ID: {available_id}\n"
                    f"➥ Rarity: {rarity_text}"
                )
            except Exception as e:
                await message.reply_text(f"Character Upload Unsuccessful. Error: {str(e)}")
            finally:
                try:
                    os.remove(path)  # Clean up the downloaded file
                except:
                    pass
        else:
            await message.reply_text("Please reply to a photo, document, or video.")


