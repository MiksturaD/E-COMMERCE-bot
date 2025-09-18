from __future__ import annotations  # Отложенная оценка аннотаций

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton  # Типы обновлений и reply-клавиатура
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters  # Хендлеры и фильтры
import phonenumbers  # Валидация телефонных номеров

from ..database import SessionLocal  # Сессия БД
from ..services.cart_service import CartService  # Сервис корзины
from ..services.order_service import OrderService  # Сервис заказов

DELIVERY_OPTIONS = ["Курьер", "Самовывоз"]  # Варианты доставки

async def cb_checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Кнопка «Оформить заказ»
    query = update.callback_query  # Callback
    await query.answer()  # Подтверждаем нажатие
    await ask_name(update, context)  # Переходим к запросу имени

async def cmd_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Команда /checkout
    await ask_name(update, context)  # Запрашиваем имя

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Шаг 1: имя
    context.user_data.clear()  # Чистим временное состояние диалога
    text = "Введите ваше имя:"  # Сообщение
    await _reply(update, text)  # Отправляем
    context.user_data["state"] = "name"  # Сохраняем состояние

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Шаг 2: телефон
    text = "Введите телефон (с кодом страны):"  # Сообщение
    await _reply(update, text)  # Отправляем
    context.user_data["state"] = "phone"  # Состояние

async def ask_address(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Шаг 3: адрес
    text = "Введите адрес доставки:"  # Сообщение
    await _reply(update, text)  # Отправляем
    context.user_data["state"] = "address"  # Состояние

async def ask_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Шаг 4: выбор доставки
    kb = ReplyKeyboardMarkup([[KeyboardButton(opt)] for opt in DELIVERY_OPTIONS], resize_keyboard=True, one_time_keyboard=True)  # Клавиатура
    await _reply(update, "Выберите способ доставки:", reply_markup=kb)  # Отправляем
    context.user_data["state"] = "delivery"  # Состояние

async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Обработчик сообщений по этапам
    state = context.user_data.get("state")  # Текущее состояние
    text = update.message.text.strip()  # Текст пользователя
    if state == "name":  # Если ждём имя
        context.user_data["name"] = text  # Сохраняем
        await ask_phone(update, context)  # Переходим к телефону
    elif state == "phone":  # Ждём телефон
        if not _is_valid_phone(text):  # Валидация номера
            await update.message.reply_text("Неверный номер. Попробуйте снова.")  # Сообщаем об ошибке
            return  # Остаёмся на шаге телефона
        context.user_data["phone"] = text  # Сохраняем телефон
        await ask_address(update, context)  # Переходим к адресу
    elif state == "address":  # Ждём адрес
        context.user_data["address"] = text  # Сохраняем адрес
        await ask_delivery(update, context)  # Переходим к доставке
    elif state == "delivery":  # Ждём выбор доставки
        if text not in DELIVERY_OPTIONS:  # Если ввели не из списка
            await update.message.reply_text("Выберите один из предложенных вариантов.")  # Просим выбрать корректно
            return  # Остаёмся на шаге доставки
        context.user_data["delivery"] = text  # Сохраняем выбор
        await create_order_and_confirm(update, context)  # Создаём заказ

async def create_order_and_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Создание заказа и подтверждение
    tg_id = update.effective_user.id  # ID пользователя
    async with SessionLocal() as session:  # Сессия БД
        cart = CartService(session)  # Сервис корзины
        user = await cart.ensure_user(tg_id)  # Пользователь
        order_service = OrderService(session)  # Сервис заказов
        order = await order_service.create_order(  # Создаём заказ
            user,
            context.user_data["name"],
            context.user_data["phone"],
            context.user_data["address"],
            context.user_data["delivery"],
        )
        await session.commit()  # Фиксируем транзакцию
    await update.message.reply_text(  # Отправляем подтверждение
        f"Заказ оформлен! Номер заказа: {order.order_number}\nСтатус: {order.status}"
    )
    context.user_data.clear()  # Сбрасываем состояние диалога

async def _reply(update: Update, text: str, reply_markup=None):  # Утилита: ответ в зависимости от контекста
    if update.callback_query:  # Если это callback
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)  # Редактируем сообщение
    else:  # Иначе обычный ответ
        await update.message.reply_text(text, reply_markup=reply_markup)  # Отвечаем пользователю

def _is_valid_phone(s: str) -> bool:  # Проверка валидности телефона через phonenumbers
    try:
        parsed = phonenumbers.parse(s, None)  # Парсим номер
        return phonenumbers.is_valid_number(parsed)  # Проверяем валидность
    except Exception:
        return False  # В случае ошибок парсинга

handlers = [  # Регистрируемые хендлеры
    CallbackQueryHandler(cb_checkout_start, pattern=r"^checkout:start$"),  # Кнопка «Оформить заказ»
    CommandHandler("checkout", cmd_checkout),  # Команда /checkout
    MessageHandler(filters.TEXT & ~filters.COMMAND, message_router),  # Роутинг текстовых сообщений по шагам
] 