from __future__ import annotations  # Отложенная оценка аннотаций

from sqlalchemy import select  # Конструктор SELECT
from sqlalchemy.ext.asyncio import AsyncSession  # Асинхронная сессия

from ..models import Category, Product, User  # ORM-модели

class AdminService:  # Сервис административных операций
    def __init__(self, session: AsyncSession, admin_ids: list[int]):  # Принимает сессию и список ID админов
        self.session = session  # Сохраняем сессию
        self.admin_ids = set(admin_ids)  # Множество ID админов для быстрого поиска

    def is_admin(self, tg_user_id: int) -> bool:  # Проверка прав администратора
        return tg_user_id in self.admin_ids  # Возвращаем True, если ID в списке админов

    async def add_category(self, name: str) -> Category:  # Добавить категорию
        category = Category(name=name)  # Создаём запись категории
        self.session.add(category)  # Добавляем в сессию
        await self.session.flush()  # Фиксируем для получения id
        return category  # Возвращаем категорию

    async def add_product(
        self,
        title: str,
        description: str,
        price_cents: int,
        category_name: str | None = None,
        photo_url: str | None = None,
    ) -> Product:  # Добавить товар
        category = None  # Категория по умолчанию
        if category_name:  # Если передано имя категории — ищем её
            res = await self.session.execute(select(Category).where(Category.name == category_name))  # Ищем по имени
            category = res.scalar_one_or_none()  # Категория или None
            if not category:  # Если не нашли — создаём новую
                category = Category(name=category_name)
                self.session.add(category)
                await self.session.flush()
        product = Product(
            title=title,
            description=description,
            price_cents=price_cents,
            category_id=category.id if category else None,
            photo_url=photo_url,
            is_active=True,
        )  # Собираем объект товара
        self.session.add(product)  # Добавляем в сессию
        await self.session.flush()  # Фиксируем для присвоения id
        return product  # Возвращаем товар

    async def edit_product(self, product_id: int, field: str, value: str) -> bool:  # Редактировать товар
        res = await self.session.execute(select(Product).where(Product.id == product_id))  # Ищем товар
        product = res.scalar_one_or_none()  # Товар или None
        if not product:  # Если не найден — False
            return False
        if field == "title":  # Изменение названия
            product.title = value
        elif field == "description":  # Изменение описания
            product.description = value
        elif field == "price":  # Изменение цены (рубли -> копейки)
            product.price_cents = int(float(value) * 100)
        elif field == "active":  # Активен/неактивен
            product.is_active = value.lower() in {"1", "true", "yes"}
        elif field == "category":  # Переназначение категории
            res = await self.session.execute(select(Category).where(Category.name == value))  # Ищем категорию по имени
            category = res.scalar_one_or_none()  # Категория или None
            if not category:  # Если нет — создаём
                category = Category(name=value)
                self.session.add(category)
                await self.session.flush()
            product.category_id = category.id  # Привязываем к товару
        elif field == "photo":  # Изменение фото
            product.photo_url = value
        else:  # Неизвестное поле
            return False
        return True  # Успех 