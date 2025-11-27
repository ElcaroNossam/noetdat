"""
Minimal Telegram bot that responds to /start and shows the chat id.

This bot does NOT need Django models; it's only used so that users can
discover their chat id and paste it into the alert form on the site.

Run from the project root:

    TELEGRAM_BOT_TOKEN=... python scripts/telegram_bot.py
"""

import asyncio
import os
import signal
import sys

# Fix for systemd event loop issues
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    # nest_asyncio not installed, will use manual event loop handling
    pass

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else None
    if chat_id is None:
        return
    text = (
        f"Привет, {update.effective_user.first_name or ''}!\n\n"
        f"Твой Telegram chat_id: <code>{chat_id}</code>\n\n"
        "Скопируй этот id и вставь его в форму создания алерта на сайте, "
        "чтобы получать уведомления по выбранным метрикам."
    )
    await update.message.reply_html(text)


async def main() -> None:
    """Main async function that sets up and runs the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN env var is required")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    print("Telegram bot is running. Press Ctrl+C to stop.")
    
    try:
        await app.run_polling(
            drop_pending_updates=True,
            stop_signals=(signal.SIGINT, signal.SIGTERM),
        )
    except KeyboardInterrupt:
        print("\nBot stopped.")
    except Exception as e:
        print(f"Bot error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # For systemd compatibility
    # nest_asyncio allows us to use asyncio.run() even if an event loop is already running
    # This fixes the "RuntimeError: This event loop is already running" error
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


