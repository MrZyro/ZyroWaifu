# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import random
import requests
from TEAMZYRO import *

emojis = ["👍", "😘", "❤️", "🔥", "🥰", "🤩", "💘", "😏", "🤯", "⚡️", "🏆", "🤭", "🎉"]

async def react_to_message(chat_id, message_id):
    # Choose a random emoji from the list
    random_emoji = random.choice(emojis)
    
    url = f'https://api.telegram.org/bot{TOKEN}/setMessageReaction'

    # Parameters for the request
    params = {
        'chat_id': chat_id,
        'message_id': message_id,
        'reaction': [{
            "type": "emoji",
            "emoji": random_emoji
        }]
    }

    response = requests.post(url, json=params)

    if response.status_code == 200:
        print("Reaction set successfully!")
    else:
        print(f"Failed to set reaction. Status code: {response.status_code}")

