# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import requests
from TEAMZYRO import TOKEN

CHAT_ID = -100
BOT_USERNAME = "@Gaming\\_X\\_World\\_Bot"  # Escaped underscores for bot username
OWNER_NAME = "@sukuna\\_dev"  # Escaped underscores for owner's username
IMAGE_URL = "https://files.catbox.moe/ehv507.jpeg"

def send_start_message():
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    caption = """🤖 *Bot has started successfully\\!*\n\n
🧑‍💻 *Owner:* {OWNER_NAME}\n\n
🚀 *Status:* All systems are operational\\!"""
    caption = caption.format(OWNER_NAME=OWNER_NAME)  # Format placeholders
    payload = {
        "chat_id": CHAT_ID,
        "photo": IMAGE_URL,
        "caption": caption,
        "parse_mode": "MarkdownV2"  # Use MarkdownV2 for proper escaping
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        print("Start message sent successfully.")
    except requests.exceptions.RequestException as e:
        if response is not None:
            print(f"Error response: {response.text}")
        print(f"Failed to send start message: {e}")

