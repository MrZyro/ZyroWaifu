# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

# ------------------------------ IMPORTS ---------------------------------
import logging
import os
from telegram.ext import Application
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters as f
#from pyrogram.types import x
from aiogram import Bot, Dispatcher, types

# --------------------------- LOGGING SETUP ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler(),
    ],
)

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("telegram").setLevel(logging.ERROR)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

# ---------------------------- CONFIGURATION -----------------------------
from config import (
    api_id, api_hash, TOKEN, BOT_LOGGING, DATABASE_ID, FORCE_JOIN,
    mongo_url, backup_mongo_url, DB_NAME, SUPPORT_CHAT, UPDATE_CHAT, OWNER_ID,
    MUSJ_JOIN, IMGBB_API_KEY, START_MEDIA, PHOTO_URL, STATS_IMG
) 

FORCE_JOIN_LINK = "https://t.me/oneforall_support"  # Updated dynamically on bot startup

# --------------------- TELEGRAM BOT CONFIGURATION -----------------------
command_filter = f.create(lambda _, __, message: message.text and message.text.startswith("/"))
application = Application.builder().token(TOKEN).build()
ZYRO = Client("Shivu", api_id=api_id, api_hash=api_hash, bot_token=TOKEN)
bot = Bot(token=TOKEN)
dp = Dispatcher()
# -------------------------- DATABASE SETUP ------------------------------
ddw = AsyncIOMotorClient(mongo_url)
db = ddw[DB_NAME]
collection = db['anime_characters_lol']
user_totals_collection = db['user_totals_lmaoooo']
user_collection = db["user_collection_lmaoooo"]
group_user_totals_collection = db['group_user_totalsssssss']
top_global_groups_collection = db['top_global_groups']
pm_users = db['total_pm_users']
discounts_collection = db['discounts']
# -------------------------- GLOBAL VARIABLES ----------------------------
app = ZYRO

x = 0000000
# --------------------------- STRIN ---------------------------------------
locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}
last_user = {}
warned_users = {}
user_cooldowns = {}
user_nguess_progress = {}
user_guess_progress = {}
normal_message_counts = {}  

# -------------------------- POWER SETUP --------------------------------
from TEAMZYRO.unit.zyro_ban import *
from TEAMZYRO.unit.zyro_sudo import *
from TEAMZYRO.unit.zyro_react import *
from TEAMZYRO.unit.zyro_log import *
from TEAMZYRO.unit.zyro_send_img import *
from TEAMZYRO.unit.zyro_rarity import *
# ------------------------------------------------------------------------

async def PLOG(text: str):
    await app.send_message(
       chat_id=BOT_LOGGING,
       text=text
   )

# ---------------------------- END OF CODE ------------------------------


backup_ddw = AsyncIOMotorClient(backup_mongo_url)

