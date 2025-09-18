from __future__ import annotations  # Отложенная оценка аннотаций типов

from telegram import InlineKeyboardButton, InlineKeyboardMarkup  # Кнопки и разметка inline-клавиатур
from typing import Iterable  # Типизация коллекций

PAGE_SIZE = 6  # Сколько товаров показывать на одной странице

def categories_kb(categories: Iterable[tuple[int, str]]):  # Клавиатура со списком категорий
    buttons = []  # Список строк кнопок
    row = []  # Текущая строка
    for cat_id, name in categories:  # Идём по категориям
        row.append(InlineKeyboardButton(name, callback_data=f"cat:{cat_id}"))  # Кнопка категории
        if len(row) == 2:  # По две кнопки в строке
            buttons.append(row)  # Добавляем строку в клавиатуру
            row = []  # Сбрасываем строку
    if row:  # Если остались кнопки в строке
        buttons.append(row)  # Добавляем последнюю строку
    return InlineKeyboardMarkup(buttons)  # Возвращаем разметку

def products_kb(products: list[tuple[int, str]], category_id: int, page: int, total_pages: int):  # Клавиатура списка товаров
    buttons = []  # Список строк кнопок
    for prod_id, title in products:  # Для каждого товара
        buttons.append([InlineKeyboardButton(title, callback_data=f"prd:{prod_id}")])  # Кнопка на отдельной строке
    nav = []  # Навигационная строка
    if page > 1:  # Кнопка назад
        nav.append(InlineKeyboardButton("◀️", callback_data=f"page:cat:{category_id}:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page}/{total_pages}", callback_data="noop"))  # Индикатор страницы
    if page < total_pages:  # Кнопка вперёд
        nav.append(InlineKeyboardButton("▶️", callback_data=f"page:cat:{category_id}:{page+1}"))
    if nav:  # Если навигация есть
        buttons.append(nav)  # Добавляем строку навигации
    buttons.append([InlineKeyboardButton("🛒 Корзина", callback_data="cart:view")])  # Переход в корзину
    return InlineKeyboardMarkup(buttons)  # Возвращаем разметку

def product_detail_kb(product_id: int):  # Клавиатура карточки товара
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ В корзину", callback_data=f"add:{product_id}"),  # Добавить товар в корзину
        ],
        [InlineKeyboardButton("🛒 Корзина", callback_data="cart:view")],  # Открыть корзину
    ])

def cart_kb(items: list[tuple[int, str, int]]):  # Клавиатура корзины с изменением количества
    buttons = []  # Список строк
    for product_id, title, qty in items:  # Для каждого товара в корзине
        buttons.append([
            InlineKeyboardButton("➖", callback_data=f"qty:{product_id}:-1"),  # Уменьшить количество
            InlineKeyboardButton(f"{title}: {qty}", callback_data="noop"),  # Показ количества
            InlineKeyboardButton("➕", callback_data=f"qty:{product_id}:1"),  # Увеличить количество
            InlineKeyboardButton("🗑️", callback_data=f"rem:{product_id}"),  # Удалить из корзины
        ])
    buttons.append([InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout:start")])  # Перейти к оформлению
    return InlineKeyboardMarkup(buttons)  # Возвращаем клавиатуру 