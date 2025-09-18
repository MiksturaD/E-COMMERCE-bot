from __future__ import annotations  # Отложенная оценка аннотаций

from telegram import Update  # Тип обновления
from telegram.ext import ContextTypes, CommandHandler  # Хендлеры команд и контекст

from ..database import SessionLocal  # Сессии БД
from ..services.admin_service import AdminService  # Админ-сервис
from ..services.order_service import OrderService  # Сервис заказов
from ..config import settings  # Настройки (ADMIN_IDS)

async def cmd_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Добавить категорию
    async with SessionLocal() as session:  # Сессия БД
        admin = AdminService(session, settings.admin_ids)  # Админ-сервис
        if not admin.is_admin(update.effective_user.id):  # Проверяем права
            await update.message.reply_text("Недостаточно прав")  # Сообщаем об отказе
            return  # Выходим
        name = " ".join(context.args)  # Имя категории из аргументов
        if not name:  # Если не указано имя
            await update.message.reply_text("Использование: /add_category <name>")  # Подсказка
            return  # Выходим
        category = await admin.add_category(name)  # Создаём категорию
        await session.commit()  # Фиксируем
    await update.message.reply_text(f"Категория добавлена: {category.name}")  # Ответ пользователю

async def cmd_add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Добавить товар
    async with SessionLocal() as session:  # Сессия БД
        admin = AdminService(session, settings.admin_ids)  # Админ-сервис
        if not admin.is_admin(update.effective_user.id):  # Проверка прав
            await update.message.reply_text("Недостаточно прав")  # Отказ
            return
        text = " ".join(context.args)  # Входные данные
        try:
            title, description, price_str, category, *rest = text.split("|")  # Парсим поля через |
            photo = rest[0] if rest else None  # Необязательный URL фото
            product = await admin.add_product(  # Создаём товар
                title.strip(), description.strip(), int(float(price_str) * 100), category.strip() or None, photo
            )
            await session.commit()  # Фиксируем
            await update.message.reply_text(f"Товар добавлен: {product.title} (ID: {product.id})")  # Успех
        except Exception:  # Любая ошибка парсинга/создания
            await update.message.reply_text("Использование: /add_product <title>|<description>|<price>|<category>|[photo_url]")  # Подсказка

async def cmd_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Редактировать товар
    async with SessionLocal() as session:  # Сессия БД
        admin = AdminService(session, settings.admin_ids)  # Админ-сервис
        if not admin.is_admin(update.effective_user.id):  # Проверка прав
            await update.message.reply_text("Недостаточно прав")  # Отказ
            return
        if len(context.args) < 3:  # Проверяем наличие всех аргументов
            await update.message.reply_text("Использование: /edit_product <id> <field> <value>")  # Подсказка
            return
        product_id = int(context.args[0])  # ID товара
        field = context.args[1]  # Поле к изменению
        value = " ".join(context.args[2:])  # Новое значение
        ok = await admin.edit_product(product_id, field, value)  # Выполняем изменение
        await session.commit()  # Фиксируем
    await update.message.reply_text("OK" if ok else "Неизвестное поле")  # Ответ об успехе/ошибке

async def cmd_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Список заказов
    async with SessionLocal() as session:  # Сессия БД
        admin = AdminService(session, settings.admin_ids)  # Админ-сервис
        if not admin.is_admin(update.effective_user.id):  # Проверка прав
            await update.message.reply_text("Недостаточно прав")  # Отказ
            return
        status = context.args[0] if context.args else None  # Необязательный фильтр по статусу
        orders = await OrderService(session).list_orders(status)  # Получаем список
    if not orders:  # Если пусто
        await update.message.reply_text("Заказов нет")  # Сообщаем
        return
    lines = [f"#{o.id} {o.order_number} {o.status} {o.total_cents/100:.2f} ₽" for o in orders]  # Форматирование строк
    await update.message.reply_text("\n".join(lines))  # Отправляем список

async def cmd_set_status(update: Update, context: ContextTypes.DEFAULT_TYPE):  # Смена статуса заказа
    async with SessionLocal() as session:  # Сессия БД
        admin = AdminService(session, settings.admin_ids)  # Админ-сервис
        if not admin.is_admin(update.effective_user.id):  # Проверка прав
            await update.message.reply_text("Недостаточно прав")  # Отказ
            return
        if len(context.args) < 2:  # Проверяем аргументы
            await update.message.reply_text("Использование: /set_status <id> <status>")  # Подсказка
            return
        order_id = int(context.args[0])  # ID заказа
        status = context.args[1]  # Новый статус
        await OrderService(session).set_status(order_id, status)  # Обновляем статус
        await session.commit()  # Фиксируем
    await update.message.reply_text("Статус обновлён")  # Ответ пользователю

handlers = [  # Регистрируемые хендлеры админа
    CommandHandler("add_category", cmd_add_category),  # Добавить категорию
    CommandHandler("add_product", cmd_add_product),  # Добавить товар
    CommandHandler("edit_product", cmd_edit_product),  # Редактировать товар
    CommandHandler("orders", cmd_orders),  # Список заказов
    CommandHandler("set_status", cmd_set_status),  # Сменить статус заказа
] 