from __future__ import annotations  # Отложенная оценка аннотаций

from telegram import Update, InputMediaPhoto  # Типы обновлений и медиа
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler  # Хендлеры и контекст

from ..database import SessionLocal  # Фабрика сессий БД
from ..services.catalog_service import CatalogService  # Сервис каталога
from ..keyboards import categories_kb, products_kb, product_detail_kb  # Фабрики клавиатур
from ..logger import logger  # Логгер

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):  # /start — показываем категории
    await show_categories(update, context)  # Переиспользуем функцию

async def cmd_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):  # /catalog — показываем категории
    await show_categories(update, context)  # Переиспользуем функцию

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Универсальный показ категорий
    async with SessionLocal() as session:  # Открываем сессию БД
        service = CatalogService(session)  # Инициализируем сервис
        cats = await service.list_categories()  # Получаем список категорий
        kb = categories_kb([(c.id, c.name) for c in cats])  # Сборка клавиатуры
    text = "Выберите категорию:" if cats else "Категории пока не созданы."  # Текст сообщения
    if update.callback_query:  # Если вызвано из callback
        await update.callback_query.edit_message_text(text, reply_markup=kb)  # Редактируем сообщение
    else:  # Если это команда
        await update.message.reply_text(text, reply_markup=kb)  # Отвечаем новым сообщением

async def cb_open_category(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Открыть товары категории
    query = update.callback_query  # Получаем callback
    _, cat_id_str = query.data.split(":")  # Разбираем payload
    cat_id = int(cat_id_str)  # Ид категории
    page = 1  # Начинаем с первой страницы
    async with SessionLocal() as session:  # Сессия БД
        service = CatalogService(session)  # Сервис
        products, total_pages = await service.list_products(cat_id, page)  # Товары и число страниц
        kb = products_kb([(p.id, p.title) for p in products], cat_id, page, total_pages)  # Клавиатура
    await query.edit_message_text(f"Товары в категории:", reply_markup=kb)  # Обновляем сообщение

async def cb_page(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Пагинация
    query = update.callback_query  # Callback
    _, what, id_str, page_str = query.data.split(":")  # Разбор payload
    page = int(page_str)  # Страница
    if what == "cat":  # Пагинация в категории
        cat_id = int(id_str)  # Категория
        async with SessionLocal() as session:  # Сессия БД
            service = CatalogService(session)  # Сервис
            products, total_pages = await service.list_products(cat_id, page)  # Получаем соответствующую страницу
            kb = products_kb([(p.id, p.title) for p in products], cat_id, page, total_pages)  # Клавиатура
        await query.edit_message_reply_markup(reply_markup=kb)  # Меняем только клавиатуру

async def cb_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Карточка товара
    query = update.callback_query  # Callback
    _, product_id_str = query.data.split(":")  # Разбор payload
    product_id = int(product_id_str)  # ID товара
    async with SessionLocal() as session:  # Сессия БД
        service = CatalogService(session)  # Сервис
        product = await service.get_product(product_id)  # Получаем товар
    if not product:  # Если не нашли
        await query.answer("Товар не найден", show_alert=True)  # Показываем алерт
        return  # Выходим
    text = f"{product.title}\n\n{product.description}\n\nЦена: {product.price_cents/100:.2f} ₽"  # Текст карточки
    kb = product_detail_kb(product.id)  # Клавиатура карточки
    if product.photo_url:  # Если есть фото
        await query.message.edit_media(  # Меняем медиа сообщения
            media=InputMediaPhoto(media=product.photo_url, caption=text),  # Фото с подписью
            reply_markup=kb,  # Клавиатура
        )
    else:  # Если фото нет
        await query.edit_message_text(text, reply_markup=kb)  # Меняем только текст

handlers = [  # Список хендлеров для регистрации
    CommandHandler("start", cmd_start),  # Команда /start
    CommandHandler("catalog", cmd_catalog),  # Команда /catalog
    CallbackQueryHandler(cb_open_category, pattern=r"^cat:\d+$"),  # Открыть категорию
    CallbackQueryHandler(cb_product_detail, pattern=r"^prd:\d+$"),  # Карточка товара
    CallbackQueryHandler(cb_page, pattern=r"^page:cat:\d+:\d+$"),  # Пагинация по категориям
] 