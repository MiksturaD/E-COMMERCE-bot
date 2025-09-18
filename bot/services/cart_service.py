from __future__ import annotations  # Отложенная оценка аннотаций

from sqlalchemy import select, delete  # Конструкторы SELECT и DELETE
from sqlalchemy.ext.asyncio import AsyncSession  # Асинхронная сессия

from ..models import CartItem, Product, User  # ORM-модели корзины, товара и пользователя

class CartService:  # Сервис работы с корзиной
    def __init__(self, session: AsyncSession):  # Принимаем асинхронную сессию
        self.session = session  # Сохраняем сессию

    async def ensure_user(self, tg_id: int) -> User:  # Гарантируем наличие пользователя в БД
        res = await self.session.execute(select(User).where(User.tg_id == tg_id))  # Ищем пользователя по Telegram ID
        user = res.scalar_one_or_none()  # Получаем пользователя или None
        if not user:  # Если нет — создаём
            user = User(tg_id=tg_id)  # Новый пользователь
            self.session.add(user)  # Добавляем в сессию
            await self.session.flush()  # Фиксируем для получения id
        return user  # Возвращаем пользователя

    async def add_to_cart(self, user: User, product_id: int, qty: int = 1) -> None:  # Добавить товар в корзину
        res = await self.session.execute(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)  # Ищем позицию в корзине
        )
        item = res.scalar_one_or_none()  # Позиция или None
        if item:  # Если позиция уже есть — увеличиваем количество
            item.quantity = max(1, item.quantity + qty)  # Не опускаемся ниже 1
        else:  # Иначе добавляем новую позицию
            self.session.add(CartItem(user_id=user.id, product_id=product_id, quantity=max(1, qty)))  # Добавляем новую запись

    async def change_qty(self, user: User, product_id: int, delta: int) -> None:  # Изменить количество позиции
        res = await self.session.execute(
            select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)  # Находим позицию
        )
        item = res.scalar_one_or_none()  # Позиция или None
        if not item:  # Если позиции нет — ничего не делаем
            return
        item.quantity += delta  # Меняем количество
        if item.quantity <= 0:  # Если стало 0 или меньше — удаляем позицию
            await self.remove_from_cart(user, product_id)

    async def remove_from_cart(self, user: User, product_id: int) -> None:  # Удалить товар из корзины
        await self.session.execute(
            delete(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id)  # Удаляем запись
        )

    async def get_cart(self, user: User) -> list[tuple[Product, int]]:  # Получить содержимое корзины
        res = await self.session.execute(
            select(CartItem, Product).
            join(Product, Product.id == CartItem.product_id).
            where(CartItem.user_id == user.id)  # Джоин с товарами для получения данных
        )
        items: list[tuple[Product, int]] = []  # Список (товар, количество)
        for item, product in res.all():  # Идём по результату
            items.append((product, item.quantity))  # Собираем кортеж
        return items  # Возвращаем список позиций

    @staticmethod
    def calculate_total(items: list[tuple[Product, int]]) -> int:  # Подсчитать итог по корзине в копейках
        return sum(prod.price_cents * qty for prod, qty in items)  # Сумма (цена * количество) 