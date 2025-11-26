"""
Minimal Telegram bot that responds to /start and shows the chat id.

This bot does NOT need Django models; it's only used so that users can
discover their chat id and paste it into the alert form on the site.

Run from the project root:

    TELEGRAM_BOT_TOKEN=... python scripts/telegram_bot.py
"""

import asyncio
import os

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
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN env var is required")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))

    print("Telegram bot is running. Press Ctrl+C to stop.")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())


