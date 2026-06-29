# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import re
from cachetools import TTLCache
from TEAMZYRO import user_collection, collection

# Caching to reduce database queries but with shorter TTL for freshness
all_characters_cache = TTLCache(maxsize=10000, ttl=300)  # Reduced from 10 hours to 5 minutes
user_collection_cache = TTLCache(maxsize=10000, ttl=30)  # Reduced from 1 minute to 30 seconds

async def get_user_collection(user_id):
    """Get user collection from database with forced refresh option"""
    user_id = str(user_id)  # Ensure consistent type
    if user_id in user_collection_cache:
        return user_collection_cache[user_id]
    
    user = await user_collection.find_one({'id': int(user_id)})
    if user:
        user_collection_cache[user_id] = user
    return user

async def search_characters(query, force_refresh=False):
    """Search characters based on name or anime with refresh option"""
    cache_key = f"search_{query.lower()}"
    if not force_refresh and cache_key in all_characters_cache:
        return all_characters_cache[cache_key]
    
    regex = re.compile(query, re.IGNORECASE)
    characters = await collection.find({"$or": [
        {"name": regex},
        {"anime": regex},
        {"aliases": regex}  # Added support for aliases
    ]}).to_list(length=None)
    
    all_characters_cache[cache_key] = characters
    return characters

async def get_all_characters(force_refresh=False):
    """Get all characters with refresh option"""
    if not force_refresh and 'all_characters' in all_characters_cache:
        return all_characters_cache['all_characters']
    
    characters = await collection.find({}).to_list(length=None)
    all_characters_cache['all_characters'] = characters
    return characters

async def refresh_character_caches():
    """Force refresh all caches"""
    all_characters_cache.clear()
    user_collection_cache.clear()
