from pyrogram import Client, filters
from pyrogram.types import Message
from pymongo import ReturnDocument
from TEAMZYRO import collection, SUDO, app, user_collection
from TEAMZYRO.unit.zyro_rarity import rarity_map  # Importing rarity_map
from TEAMZYRO import require_power 
SUDO_USERS = SUDO

@app.on_message(filters.command("gdelete"))
@require_power("delete_character")
async def delete_handler(client, message):
    try:
        # Extract arguments from the command
        args = message.text.split()
        if len(args) != 2:
            await message.reply_text("Incorrect format... Please use: /gdelete ID")
            return

        character_id = args[1]

        # Find and delete the character from the main collection
        character = await collection.find_one_and_delete({'id': character_id})
        if character:
            # Remove the character from all users' collections
            update_result = await user_collection.update_many(
                {'characters.id': character_id},
                {'$pull': {'characters': {'id': character_id}}}
            )

            await message.reply_text(
                f"Character with ID {character_id} deleted successfully from the database.\n"
                f"Removed from {update_result.modified_count} user collections."
            )
        else:
            await message.reply_text(f"Character with ID {character_id} not found in the database.")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")

import time

@app.on_message(filters.command("gupdate"))
@require_power("update_character")
async def update(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) != 4:
            await message.reply_text('Incorrect format. Please use: /gupdate id field new_value')
            return

        character_id = args[1]
        field_to_update = args[2]
        new_value = args[3]

        # Validate field
        valid_fields = ['img_url', 'name', 'anime', 'rarity']
        if field_to_update not in valid_fields:
            await message.reply_text(f'Invalid field. Please use one of the following: {", ".join(valid_fields)}')
            return

        # Process the new value
        if field_to_update in ['name', 'anime']:
            new_value = new_value.replace('-', ' ').title()
        elif field_to_update == 'rarity':
            try:
                new_value = rarity_map[int(new_value)]  # Use rarity_map
            except (KeyError, ValueError):
                await message.reply_text('Invalid rarity. Please use a valid number between 1-12 for rarity.')
                return

        # Update the character in the main collection
        result = await collection.update_one({'id': character_id}, {'$set': {field_to_update: new_value}})
        if result.modified_count == 0:
            await message.reply_text('Character not found or no changes made.')
            return

        # Fetch users who have the character
        users_cursor = user_collection.find({'characters.id': character_id})
        total_users = await user_collection.count_documents({'characters.id': character_id})

        if total_users == 0:
            await message.reply_text('sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇ ✅')
            return

        # Send initial message for progress
        progress_message = await message.reply_text('Updating: 0% completed...')
        updated_count = 0
        progress_threshold = 10  # Show progress every 10%
        next_progress_update = progress_threshold

        async for user in users_cursor:
            await user_collection.update_one(
                {'_id': user['_id'], 'characters.id': character_id},
                {'$set': {f'characters.$.{field_to_update}': new_value}}
            )
            updated_count += 1

            # Show progress at every 10% interval
            progress = (updated_count / total_users) * 100
            if progress >= next_progress_update:
                await progress_message.edit_text(f'Updating: {int(progress)}% completed...')
                next_progress_update += progress_threshold
                time.sleep(1)  # Add a 1-second delay

        # Final message with the total count
        await progress_message.edit_text('Updating: 100% completed.')
        await message.reply_text(f'sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇ ✅ \nTotal users updated: {updated_count}/{total_users}')

    except Exception as e:
        await message.reply_text(f'Error: {str(e)}')

import time

@app.on_message(filters.command("maxupdate"))
@require_power("update_character")
async def update_multiple(client: Client, message: Message):
    try:
        args = message.text.split()
        if len(args) < 4:
            await message.reply_text('Incorrect format. Use: /gupdate id1,id2,id3 field new_value')
            return

        # Parse multiple character IDs
        character_ids = args[1].split(',')
        field_to_update = args[2]
        new_value = ' '.join(args[3:])

        # Validate field
        valid_fields = ['img_url', 'name', 'anime', 'rarity']
        if field_to_update not in valid_fields:
            await message.reply_text(f'Invalid field. Use one of: {", ".join(valid_fields)}')
            return

        # Process the new value
        if field_to_update in ['name', 'anime']:
            new_value = new_value.replace('-', ' ').title()
        elif field_to_update == 'rarity':
            try:
                new_value = rarity_map[int(new_value)]  # Use rarity_map
            except (KeyError, ValueError):
                await message.reply_text('Invalid rarity. Use a valid number between 1-12 for rarity.')
                return

        # Track total updates
        total_characters = len(character_ids)
        updated_characters = 0
        total_users_updated = 0

        # Initial progress message
        progress_message = await message.reply_text('Updating: 0% completed...')
        next_progress_update = 10  # Update progress every 10%

        for i, character_id in enumerate(character_ids, start=1):
            # Update the character in the main collection
            result = await collection.update_one({'id': character_id}, {'$set': {field_to_update: new_value}})
            if result.modified_count == 0:
                continue

            # Fetch users with the character
            users_cursor = user_collection.find({'characters.id': character_id})
            async for user in users_cursor:
                await user_collection.update_one(
                    {'_id': user['_id'], 'characters.id': character_id},
                    {'$set': {f'characters.$.{field_to_update}': new_value}}
                )
                total_users_updated += 1

            updated_characters += 1

            # Update progress percentage
            progress = (i / total_characters) * 100
            if progress >= next_progress_update:
                await progress_message.edit_text(f'Updating: {int(progress)}% completed...')
                next_progress_update += 10
                time.sleep(1)

        # Final update after all characters
        await progress_message.edit_text('Updating: 100% completed.')
        await message.reply_text(
            f'sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘᴅᴀᴛᴇ ✅ \nTotal characters updated: {updated_characters}/{total_characters}. '
            f'Total users updated: {total_users_updated}.'
        )

    except Exception as e:
        await message.reply_text(f'Error: {str(e)}')


@app.on_message(filters.command("findani") & filters.user(SUDO_USERS))
async def find_anime_ids(client: Client, message: Message):
    try:
        # Extract anime name from the command
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text("Please provide an anime name. Usage: /findani {anime name}")
            return

        anime_name = args[1].strip().lower()

        # Search for characters with the given anime name
        characters_cursor = collection.find({"anime": {"$regex": f"^{anime_name}$", "$options": "i"}}, {"id": 1})
        character_ids = [str(character['id']) for character in await characters_cursor.to_list(length=None)]

        if not character_ids:
            await message.reply_text(f"No characters found for anime name: {anime_name}")
        else:
            ids_list = ",".join(character_ids)
            await message.reply_text(f"Character IDs for '{anime_name}':\n{ids_list}")

    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")
