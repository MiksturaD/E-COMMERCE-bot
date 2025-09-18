from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/catalog — каталог\n/cart — корзина\n/checkout — оформить заказ\n/help — помощь"
    )

handlers = [CommandHandler("help", cmd_help)] 