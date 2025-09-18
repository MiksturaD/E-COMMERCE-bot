from __future__ import annotations  # Отложенная оценка аннотаций

from telegram import Update  # Обновление Telegram
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler  # Хендлеры и контекст

from ..database import SessionLocal  # Сессии БД
from ..services.cart_service import CartService  # Сервис корзины
from ..services.catalog_service import CatalogService  # (опционально) сервис каталога
from ..keyboards import cart_kb  # Клавиатура корзины

async def cmd_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):  # /cart — показать корзину
    tg_id = update.effective_user.id  # Telegram ID пользователя
    async with SessionLocal() as session:  # Открываем сессию БД
        cart = CartService(session)  # Инициализируем сервис корзины
        user = await cart.ensure_user(tg_id)  # Гарантируем наличие пользователя
        items = await cart.get_cart(user)  # Получаем содержимое корзины
        await session.commit()  # Завершаем транзакцию
    if not items:  # Если корзина пуста
        text = "Корзина пуста"  # Сообщение пользователю
        if update.callback_query:  # Вызов из callback
            await update.callback_query.edit_message_text(text)  # Редактируем сообщение
        else:  # Команда
            await update.message.reply_text(text)  # Отвечаем новым сообщением
        return  # Завершаем хендлер
    kb = cart_kb([(p.id, p.title, qty) for p, qty in items])  # Сборка клавиатуры корзины
    total_rub = sum(p.price_cents * qty for p, qty in items) / 100  # Итог в рублях
    text = f"Ваша корзина. Итого: {total_rub:.2f} ₽"  # Текст итога
    if update.callback_query:  # Если callback
        await update.callback_query.edit_message_text(text, reply_markup=kb)  # Редактируем
    else:  # Иначе новое сообщение
        await update.message.reply_text(text, reply_markup=kb)

async def cb_add(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Кнопка «Добавить в корзину»
    query = update.callback_query  # Callback объект
    tg_id = update.effective_user.id  # ID пользователя
    product_id = int(query.data.split(":")[1])  # Извлекаем ID товара
    async with SessionLocal() as session:  # Сессия БД
        cart = CartService(session)  # Сервис корзины
        user = await cart.ensure_user(tg_id)  # Гарантируем пользователя
        await cart.add_to_cart(user, product_id, 1)  # Добавляем 1 шт
        await session.commit()  # Фиксируем изменения
    await query.answer("Добавлено в корзину")  # Всплывающее уведомление

async def cb_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Кнопка удаления позиции
    query = update.callback_query  # Callback
    tg_id = update.effective_user.id  # ID пользователя
    product_id = int(query.data.split(":")[1])  # ID товара
    async with SessionLocal() as session:  # Сессия БД
        cart = CartService(session)  # Сервис корзины
        user = await cart.ensure_user(tg_id)  # Пользователь
        await cart.remove_from_cart(user, product_id)  # Удаляем позицию
        await session.commit()  # Фиксируем
    await cmd_cart(update, context)  # Обновляем отображение корзины

async def cb_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Кнопки изменения количества
    query = update.callback_query  # Callback
    tg_id = update.effective_user.id  # ID пользователя
    _, product_id_str, delta_str = query.data.split(":")  # Парсим payload
    async with SessionLocal() as session:  # Сессия БД
        cart = CartService(session)  # Сервис корзины
        user = await cart.ensure_user(tg_id)  # Пользователь
        await cart.change_qty(user, int(product_id_str), int(delta_str))  # Меняем количество
        await session.commit()  # Фиксируем
    await cmd_cart(update, context)  # Обновляем корзину

handlers = [  # Регистрируемые хендлеры
    CommandHandler("cart", cmd_cart),  # Команда /cart
    CallbackQueryHandler(cb_add, pattern=r"^add:\d+$"),  # Добавить товар
    CallbackQueryHandler(cb_remove, pattern=r"^rem:\d+$"),  # Удалить позицию
    CallbackQueryHandler(cb_qty, pattern=r"^qty:\d+:-?\d+$"),  # Изменить количество
] 