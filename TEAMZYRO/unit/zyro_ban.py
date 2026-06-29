# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import time
from TEAMZYRO import *

async def check_cooldown(user_id: int) -> bool:
    if user_id in user_cooldowns:
        current_time = time.time()
        cooldown_end = user_cooldowns[user_id]
        if current_time < cooldown_end:
            return True
    return False

async def get_remaining_cooldown(user_id: int) -> int:
    if user_id in user_cooldowns:
        current_time = time.time()
        cooldown_end = user_cooldowns[user_id]
        if current_time < cooldown_end:
            return int(cooldown_end - current_time)
    return 0
