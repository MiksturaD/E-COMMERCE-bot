from __future__ import annotations  # Включает аннотации будущих версий Python (отложенная оценка типов)

import asyncio  # Модуль для работы с асинхронными задачами
from telegram.ext import Application, ApplicationBuilder  # Компоненты фреймворка python-telegram-bot

from .config import settings  # Загрузка настроек из окружения
from .logger import logger  # Глобальный логгер
from .database import init_models  # Инициализация базы данных (создание таблиц)
from .handlers import catalog as catalog_h  # Хендлеры каталога
from .handlers import cart as cart_h  # Хендлеры корзины
from .handlers import checkout as checkout_h  # Хендлеры оформления заказа
from .handlers import admin as admin_h  # Админ-команды
from .handlers import help as help_h  # Команда помощи

async def main_async():  # Точка входа (асинхронная) для запуска бота
    if not settings.bot_token:  # Проверяем, что задан токен бота
        raise RuntimeError("BOT_TOKEN is not set")  # Если нет — падаем с понятной ошибкой
    await init_models()  # Создаём таблицы БД при старте (если их ещё нет)

    app: Application = ApplicationBuilder().token(settings.bot_token).build()  # Создаём приложение Telegram бота

    for h in catalog_h.handlers + cart_h.handlers + checkout_h.handlers + admin_h.handlers + help_h.handlers:  # Регистрируем все хендлеры
        app.add_handler(h)  # Добавляем хендлер в приложение

    logger.info("Bot starting...")  # Логируем старт
    await app.initialize()  # Инициализация приложения (внутренние структуры)
    await app.start()  # Старт приложения (подготовка к приёму обновлений)
    await app.updater.start_polling(drop_pending_updates=True)  # Запуск получения апдейтов через long polling
    await app.updater.idle()  # Ожидание завершения работы (Ctrl+C)

if __name__ == "__main__":  # Если файл запущен как скрипт
    asyncio.run(main_async())  # Запускаем асинхронную точку входа 