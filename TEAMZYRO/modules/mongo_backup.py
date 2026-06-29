# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

from pyrogram import Client, filters
from pymongo import MongoClient
import os
import asyncio
import bson
from TEAMZYRO import app

def calculate_collection_size(documents):
    """
    Calculate the size of a list of documents in bytes.
    """
    return sum(len(bson.BSON.encode(doc)) for doc in documents)

@app.on_message(filters.command("mongobackup") & filters.private)
async def mongo_backup(client, message):
    try:
        # Split command arguments
        args = message.text.split()
        if len(args) != 4:
            await message.reply("Usage: /mongobackup {source_mongo_uri} {destination_mongo_uri} {database_name}")
            return

        source_mongo_uri = args[1]
        destination_mongo_uri = args[2]
        database_name = args[3]

        await message.reply(f"Connecting to source MongoDB: `{source_mongo_uri}`...")
        source_client = MongoClient(source_mongo_uri)
        source_db = source_client[database_name]

        await message.reply(f"Connecting to destination MongoDB: `{destination_mongo_uri}`...")
        dest_client = MongoClient(destination_mongo_uri)
        dest_db = dest_client[database_name]

        await message.reply(f"Starting backup of `{database_name}`...")

        total_size = 0  # Total size tracker
        for collection_name in source_db.list_collection_names():
            source_collection = source_db[collection_name]
            dest_collection = dest_db[collection_name]

            # Fetch all documents from the source collection
            documents = list(source_collection.find())
            collection_size = calculate_collection_size(documents)
            total_size += collection_size

            # Clear destination collection and insert updated documents
            dest_collection.delete_many({})  # Clear old data
            if documents:
                dest_collection.insert_many(documents)
                size_mb = collection_size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{collection_size / 1024:.2f} KB"
                await message.reply(f"Collection `{collection_name}` backed up successfully. Size: {size_str}.")
            else:
                await message.reply(f"Collection `{collection_name}` is empty. Skipping...")

        total_size_mb = total_size / (1024 * 1024)
        total_size_str = f"{total_size_mb:.2f} MB" if total_size_mb >= 1 else f"{total_size / 1024:.2f} KB"
        await message.reply(f"Backup of `{database_name}` completed successfully! Total size: {total_size_str}.")
    except Exception as e:
        await message.reply(f"An error occurred: {e}")
    finally:
        # Close MongoDB connections
        try:
            source_client.close()
            dest_client.close()
        except:
            pass

