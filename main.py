import os
import psutil
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from yt_dlp import YoutubeDL
import asyncio
import aiohttp

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
ALLOWED_GROUP = int(os.getenv("ALLOWED_GROUP"))

app = Client("leechbot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

start_time = time.time()
active_tasks = {}
authorized_users = {OWNER_ID}

def get_readable_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"

@app.on_message(filters.command("start") & filters.private)
async def start(client, message: Message):
    await message.reply("Hi, I am Ultra Pro Max Leech Bot!")

@app.on_message(filters.command("sonic"))
async def authorize_user(client, message: Message):
    if message.from_user.id != OWNER_ID:
        return
    try:
        new_user = int(message.text.split(" ", 1)[1])
        authorized_users.add(new_user)
        await message.reply(f"User {new_user} authorized!")
    except:
        await message.reply("Invalid ID")

@app.on_message(filters.command("stats"))
async def stats(client, message: Message):
    if message.chat.id != ALLOWED_GROUP:
        return
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent()
    uptime = get_readable_time(time.time() - start_time)
    await message.reply(f"Uptime: {uptime}\nCPU: {cpu}%\nRAM: {mem.percent}%")

@app.on_message(filters.command("cancel"))
async def cancel_task(client, message: Message):
    uid = message.from_user.id
    task = active_tasks.pop(uid, None)
    if task:
        task.cancel()
        await message.reply("Task cancelled.")
    else:
        await message.reply("No active task found.")

@app.on_message(filters.command("XD"))
async def download_m3u8(client, message: Message):
    uid = message.from_user.id
    if message.chat.id != ALLOWED_GROUP or uid not in authorized_users:
        return

    if uid in active_tasks:
        await message.reply("Only 1 task allowed at a time.")
        return

    url = message.text.split(" ", 1)[1]
    filename = f"{uid}_video.mp4"
    msg = await message.reply("Downloading...")

    ydl_opts = {
        'outtmpl': filename,
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'progress_hooks': [lambda d: asyncio.create_task(update_progress(d, msg))]
    }

    async def task():
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            await msg.edit_text("Upload starting...")
            await client.send_document(message.chat.id, filename)
        except Exception as e:
            await msg.edit_text(f"Error: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)
            active_tasks.pop(uid, None)

    active_tasks[uid] = asyncio.create_task(task())

async def update_progress(d, msg):
    if d['status'] == 'downloading':
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        eta = d.get("eta", 0)
        text = f"📥 Downloading: {percent}\n⚡ Speed: {speed}\n⏳ ETA: {eta}s"
        await msg.edit_text(text)

@app.on_message(filters.command("l"))
async def download_pdf(client, message: Message):
    uid = message.from_user.id
    if message.chat.id != ALLOWED_GROUP or uid not in authorized_users:
        return
    if uid in active_tasks:
        await message.reply("Only 1 task allowed at a time.")
        return

    url = message.text.split(" ", 1)[1]
    filename = f"{uid}_file.pdf"
    msg = await message.reply("Downloading PDF...")

    async def task():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    with open(filename, "wb") as f:
                        f.write(await resp.read())
            await msg.edit_text("Uploading PDF...")
            await client.send_document(message.chat.id, filename)
        except Exception as e:
            await msg.edit_text(f"Error: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)
            active_tasks.pop(uid, None)

    active_tasks[uid] = asyncio.create_task(task())

app.run()
