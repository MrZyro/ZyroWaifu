# ==========================================
# Creator: MrZyro
# Telegram: @MrZyro_dev
# GitHub: https://github.com/MrZyro
# ==========================================

import os
import asyncio
import requests
from pyrogram import filters
from TEAMZYRO import ZYRO, collection, require_power, BOT_LOGGING, IMGBB_API_KEY

UPLOAD_API = "https://api.imgbb.com/1/upload"

# ─────────────────────────────────────────────────
#  /reupload <id1> <id2> <id3> ...
#
#  Flow for each ID:
#   1. Fetch existing (broken) img_url from DB
#   2. Bot sends_photo with that URL to GLOG chat
#      → Telegram downloads from its cache
#   3. Bot downloads the photo via Telegram file_id
#   4. Re-uploads to ImgBB → gets fresh URL
#   5. Updates img_url in DB (matched by exact stored id)
#   6. Deletes the temp Telegram message
# ─────────────────────────────────────────────────


def upload_to_imgbb(file_path: str) -> str:
    """Upload a local file to ImgBB and return the public URL."""
    with open(file_path, "rb") as f:
        response = requests.post(
            UPLOAD_API,
            data={"key": IMGBB_API_KEY},
            files={"image": f},
            timeout=60,
        )
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            return data["data"]["url"]
            
    raise Exception(f"ImgBB upload failed ({response.status_code}): {response.text}")


async def find_char(char_id: str):
    """
    Try multiple ID formats because MongoDB may store as string "60"
    or zero-padded "60" or integer 60.
    """
    # Try as-is string
    char = await collection.find_one({"id": char_id})
    if char:
        return char

    # Try zero-padded string e.g. "60" → already tried, try "060"
    padded = char_id.zfill(2)
    if padded != char_id:
        char = await collection.find_one({"id": padded})
        if char:
            return char

    # Try integer
    try:
        char = await collection.find_one({"id": int(char_id)})
        if char:
            return char
    except ValueError:
        pass

    return None


@ZYRO.on_message(filters.command(["reupload"]))
@require_power("add")
async def reupload_handler(client, message):
    """
    Usage:
      /reupload 60
      /reupload 30 60 61 100
    """
    args = message.text.split()[1:]

    if not args:
        return await message.reply_text(
            "❌ **Wrong format!**\n\n"
            "Usage:\n"
            "`/reupload 60`\n"
            "`/reupload 30 60 61 100`"
        )

    status_msg = await message.reply_text(
        f"⏳ Processing **{len(args)}** character(s)…"
    )

    results = []
    success = 0
    fail    = 0

    for char_id in args:
        char_id  = char_id.strip()
        path     = None
        sent_msg = None

        try:
            # ── Step 1: Find character in DB ───────
            char = await find_char(char_id)
            if not char:
                results.append(f"❌ `{char_id}` — not found in DB")
                fail += 1
                continue

            stored_id = char.get("id")           # exact value stored in DB
            name      = char.get("name", "?")
            old_url   = char.get("img_url", "")

            if not old_url:
                results.append(f"❌ `{char_id}` ({name}) — no img_url in DB")
                fail += 1
                continue

            # ── Step 2: Send photo to BOT_LOGGING ─────────
            try:
                sent_msg = await client.send_photo(
                    chat_id=BOT_LOGGING,
                    photo=old_url,
                    caption=f"#reupload id:{char_id}"
                )
            except Exception as send_err:
                results.append(f"❌ `{char_id}` ({name}) — Telegram send failed: `{str(send_err)[:80]}`")
                fail += 1
                continue

            # ── Step 3: Download from Telegram ─────
            tmp_file = f"/tmp/reupload_{char_id}.jpg"
            path = await client.download_media(
                sent_msg.photo.file_id,
                file_name=tmp_file
            )

            if not path or not os.path.exists(path):
                raise Exception("Download from Telegram returned empty file")

            file_size = os.path.getsize(path)
            if file_size < 100:
                raise Exception(f"Downloaded file too small ({file_size} bytes) — image may be invalid")

            # ── Step 4: Upload to ImgBB ──────────
            new_url = upload_to_imgbb(path)

            # ── Step 5: Update MongoDB ─────────────
            # Match using the exact stored_id value (preserves original type)
            update_result = await collection.update_one(
                {"id": stored_id},
                {"$set": {"img_url": new_url, "status": "working"}}
            )

            if update_result.matched_count == 0:
                raise Exception(f"DB match failed for id={stored_id!r} (type={type(stored_id).__name__})")

            if update_result.modified_count == 0:
                results.append(f"⚠️ `{char_id}` ({name}) — matched but not modified (same URL?)")
            else:
                results.append(f"✅ `{char_id}` **{name}**\n   └ `{new_url}`")
                success += 1

        except Exception as e:
            results.append(f"❌ `{char_id}` — `{str(e)[:120]}`")
            fail += 1

        finally:
            # Delete temp Telegram message
            if sent_msg:
                try:
                    await sent_msg.delete()
                except Exception:
                    pass
            # Delete local file
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

            # Small delay to avoid flood
            await asyncio.sleep(0.5)

    # ── Final summary ─────────────────────────────
    summary = "\n".join(results)
    await status_msg.edit(
        f"**📦 Reupload Complete**\n"
        f"✅ Success: **{success}**  |  ❌ Failed: **{fail}**\n\n"
        f"{summary}"
    )
