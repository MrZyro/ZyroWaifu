# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import time

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from TEAMZYRO import application, is_vip_or_owner

async def ping(update: Update, context: CallbackContext) -> None:
    if not await is_vip_or_owner(update.effective_user.id):
        await update.message.reply_text("Nouu.. only Owner or VIP users can run this command..")
        return
    start_time = time.time()
    message = await update.message.reply_text('Pong!')
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 3)
    await message.edit_text(f'Pong! {elapsed_time}ms')

application.add_handler(CommandHandler("ping", ping))
