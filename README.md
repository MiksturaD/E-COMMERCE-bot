# Telegram E-Commerce Bot (Русская версия)

Производственный Telegram-бот для интернет‑магазина с полным циклом покупки: каталог, корзина, оформление заказа, список заказов и админ‑команды.

## Возможности
- Каталог: категории, список товаров, карточка товара с фото, навигация через inline‑кнопки
- Корзина: добавление/удаление, изменение количества, подсчёт итога
- Оформление заказа: имя, телефон, адрес, способ доставки, подтверждение, генерация номера заказа
- Админ: добавление/редактирование товаров и категорий, список заказов, смена статуса
- Архитектура: модульные сервисы, модели SQLAlchemy, обработка ошибок, логирование
- Документация: схема БД, команды, примеры callback‑API
- Тесты: юнит‑тесты основных сценариев

## Технологии
- Python 3.11+
- python-telegram-bot 21.x
- SQLAlchemy 2.x (SQLite, async)
- Alembic (миграции, опционально)
- pytest

## Быстрый старт

Заполните `.env`:
```
BOT_TOKEN=123456:ABC...
ADMIN_IDS=123456789,987654321
DATABASE_URL=sqlite+aiosqlite:///./shop.db
LOG_LEVEL=INFO
```
На Windows PowerShell можно скопировать вручную, если нет команды `cp`.

1) Виртуальное окружение и зависимости:
```
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

2) Инициализация БД: таблицы создаются автоматически при первом запуске. (При желании можно подключить Alembic.)

3) Запуск бота:
```
python -m bot
```

## Структура проекта
```
bot/
  __init__.py
  __main__.py
  main.py
  config.py
  logger.py
  database.py
  models.py
  keyboards.py
  handlers/
    __init__.py
    catalog.py
    cart.py
    checkout.py
    admin.py
    help.py
  services/
    __init__.py
    catalog_service.py
    cart_service.py
    order_service.py
    admin_service.py
tests/
  test_catalog.py
  test_cart.py
  test_order.py
.env.example
requirements.txt
README.md
```

## Переменные окружения
- `BOT_TOKEN`: токен Telegram‑бота
- `ADMIN_IDS`: ID администраторов через запятую
- `DATABASE_URL`: строка подключения SQLAlchemy (по умолчанию SQLite файл)
- `LOG_LEVEL`: уровень логирования (INFO/DEBUG/...)

## Схема базы данных
- `users(id, tg_id, name, phone, address, created_at)`
- `categories(id, name)`
- `products(id, title, description, price_cents, photo_url, category_id, is_active)`
- `cart_items(id, user_id, product_id, quantity)`
- `orders(id, user_id, total_cents, delivery_method, status, created_at, customer_name, customer_phone, customer_address, order_number)`
- `order_items(id, order_id, product_id, quantity, price_cents)`

См. `bot/models.py`.

## Команды пользователя
- `/start` — старт и показ каталога
- `/catalog` — открыть категории
- `/cart` — показать корзину
- `/checkout` — оформить заказ
- `/help` — помощь

## Команды администратора
- `/add_category <name>` — добавить категорию
- `/add_product <title>|<description>|<price>|<category>|[photo_url]` — добавить товар
- `/edit_product <product_id> <field> <value>` — редактировать товар
  - поля: `title|description|price|active|category|photo`
- `/orders [status]` — показать заказы (опционально фильтр по статусу)
- `/set_status <order_id> <status>` — сменить статус заказа

## Callback‑протокол (inline)
- `cat:<category_id>` — открыть товары категории
- `prd:<product_id>` — карточка товара
- `add:<product_id>` — добавить в корзину
- `rem:<product_id>` — удалить из корзины
- `qty:<product_id>:<delta>` — изменить количество
- `page:<what>:<id>:<page>` — пагинация

## Тестирование
```
pytest -q
```

## Обработка ошибок и логирование
- Loguru пишет структурированные логи в stdout
- Сервисы и хендлеры валидируют ввод и сообщают об ошибках пользователю

## Примечания
- Цены хранятся в копейках (`price_cents`) для избежания ошибок округления
- Валидация телефона через `phonenumberslite`
- Можно легко заменить SQLite на Postgres, изменив `DATABASE_URL` 