from __future__ import annotations  # Отложенная оценка аннотаций

from sqlalchemy import select, func  # Построители запросов SELECT и агрегаций
from sqlalchemy.ext.asyncio import AsyncSession  # Асинхронная сессия SQLAlchemy
from math import ceil  # Округление вверх для страниц

from ..models import Category, Product  # ORM-модели
from ..keyboards import PAGE_SIZE  # Размер страницы каталога

class CatalogService:  # Сервис каталога
    def __init__(self, session: AsyncSession):  # Принимаем асинхронную сессию БД
        self.session = session  # Сохраняем сессию

    async def list_categories(self) -> list[Category]:  # Список категорий
        stmt = select(Category).order_by(Category.name)  # Запрос категорий с сортировкой по имени
        res = await self.session.execute(stmt)  # Выполняем запрос
        return list(res.scalars().all())  # Возвращаем список объектов Category

    async def list_products(self, category_id: int, page: int = 1) -> tuple[list[Product], int]:  # Список товаров с пагинацией
        page = max(1, page)  # Минимум первая страница
        total_stmt = select(func.count()).select_from(Product).where(  # Считаем общее число товаров
            Product.category_id == category_id, Product.is_active == True  # noqa: E712  # Только активные товары категории
        )
        total = (await self.session.execute(total_stmt)).scalar_one()  # Получаем число товаров
        total_pages = max(1, ceil(total / PAGE_SIZE))  # Сколько всего страниц
        offset = (page - 1) * PAGE_SIZE  # Смещение для LIMIT/OFFSET
        stmt = (
            select(Product)
            .where(Product.category_id == category_id, Product.is_active == True)  # noqa: E712  # Фильтр
            .order_by(Product.title)  # Сортировка по названию
            .limit(PAGE_SIZE)  # Лимит на страницу
            .offset(offset)  # Смещение
        )
        res = await self.session.execute(stmt)  # Выполняем запрос
        return list(res.scalars().all()), total_pages  # Список товаров и количество страниц

    async def get_product(self, product_id: int) -> Product | None:  # Получить товар по id
        stmt = select(Product).where(Product.id == product_id, Product.is_active == True)  # noqa: E712  # Фильтр по id и активности
        res = await self.session.execute(stmt)  # Выполняем запрос
        return res.scalar_one_or_none()  # Возвращаем товар или None 