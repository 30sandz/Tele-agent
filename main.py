from utils import fetch_chat_summary
from telethon import TelegramClient, events
import config as cfg
import time
from utils import keyword_alert


app = TelegramClient('UserSession', cfg.API_ID, cfg.API_HASH)

async def main():
    await app.start()  # This will prompt for phone login on first run
    print("✅ Userbot is running!")
    await app.run_until_disconnected()
@app.on(events.NewMessage(pattern=r"^/summarize"))
async def handle_summarize(event):
    args = event.message.message.split()[1:]  # Extract command arguments
    chat_id = event.chat_id
    user_id = None
    keyword = None
    time_range = None

    # Parse arguments
    for arg in args:
        if arg.startswith("user:"):
            user_id = int(arg.split(":")[1])  # Extract user ID
        elif arg.startswith("keyword:"):
            keyword = arg.split(":")[1]  # Extract keyword
        elif arg.startswith("time:"):
            time_range = int(arg.split(":")[1])  # Extract time in hours

    # Fetch and send summary
    summary = await fetch_chat_summary(app, chat_id, limit=100, user_id=user_id, keyword=keyword, time_range=time_range)
    await event.reply(summary)

@app.on(events.NewMessage)  # Removed incoming=True
async def message_handler(event: events.NewMessage.Event):
    try:
        # Ensure the message is valid
        if not event.message or not event.message.message:
            return

        prompt = event.message.message.strip()

        chat_type = "Private Chat" if event.is_private else "Group Chat"
        print(f"📩 Received message in {chat_type}: {prompt}")

        # Ensure private messages are processed
        if event.is_private:
            print("👤 Message is from a private chat!")

        # Check for keyword alerts
        alert_message = keyword_alert(prompt)
        if alert_message:
            await event.reply(alert_message)  # Send keyword alert

    except Exception as e:
        print(f"❌ Error in message_handler: {e}")

@app.on(events.NewMessage(incoming=True))
async def debug_handler(event):
    print(f"🔹 RAW MESSAGE: {event.message}")

@app.on(events.NewMessage(pattern=r"^/keywords"))
async def manage_keywords(event):
    args = event.message.message.split()[1:]  # Extract command arguments

    if not args:
        await event.reply(f"📝 **Tracked Keywords:** {', '.join(cfg.TRACKED_KEYWORDS)}")
        return

    command = args[0].lower()
    
    if command == "add" and len(args) > 1:
        new_keyword = args[1].lower()
        if new_keyword not in cfg.TRACKED_KEYWORDS:
            cfg.TRACKED_KEYWORDS.append(new_keyword)
            await event.reply(f"✅ Added **{new_keyword}** to keyword tracking.")
        else:
            await event.reply(f"⚠️ **{new_keyword}** is already being tracked.")

    elif command == "remove" and len(args) > 1:
        remove_keyword = args[1].lower()
        if remove_keyword in cfg.TRACKED_KEYWORDS:
            cfg.TRACKED_KEYWORDS.remove(remove_keyword)
            await event.reply(f"❌ Removed **{remove_keyword}** from keyword tracking.")
        else:
            await event.reply(f"⚠️ **{remove_keyword}** is not in the tracked keywords list.")

    else:
        await event.reply("❌ Invalid command. Use `/keywords add <word>` or `/keywords remove <word>`.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
