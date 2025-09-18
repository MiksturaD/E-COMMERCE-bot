from __future__ import annotations  # Отложенная оценка аннотаций

from sqlalchemy import select  # Конструктор SELECT
from sqlalchemy.ext.asyncio import AsyncSession  # Асинхронная сессия
from datetime import datetime  # Генерация даты для номера заказа
import secrets  # Для генерации случайной части номера

from ..models import Order, OrderItem, User, Product, CartItem  # ORM-модели
from .cart_service import CartService  # Используем CartService для получения корзины

class OrderService:  # Сервис заказов
    def __init__(self, session: AsyncSession):  # Принимаем асинхронную сессию
        self.session = session  # Сохраняем сессию
        self.cart_service = CartService(session)  # Инициализируем сервис корзины

    async def create_order(
        self,
        user: User,
        customer_name: str,
        customer_phone: str,
        customer_address: str,
        delivery_method: str,
    ) -> Order:  # Создать заказ из корзины пользователя
        items = await self.cart_service.get_cart(user)  # Получаем товары из корзины
        total_cents = sum(prod.price_cents * qty for prod, qty in items)  # Считаем итог в копейках
        order_number = self._generate_order_number()  # Генерируем номер заказа
        order = Order(
            user_id=user.id,
            total_cents=total_cents,
            delivery_method=delivery_method,
            status="new",
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            order_number=order_number,
        )  # Создаём объект заказа
        self.session.add(order)  # Добавляем в сессию
        await self.session.flush()  # Фиксируем для получения order.id
        for product, qty in items:  # Создаём позиции заказа
            self.session.add(
                OrderItem(order_id=order.id, product_id=product.id, quantity=qty, price_cents=product.price_cents)
            )  # Добавляем позицию
        # clear cart
        await self.session.execute(select(CartItem).where(CartItem.user_id == user.id))  # Ненужный select (можно убрать), сохраняем как безопасный no-op
        await self.session.execute(
            CartItem.__table__.delete().where(CartItem.user_id == user.id)  # Удаляем все позиции корзины пользователя
        )
        return order  # Возвращаем заказ

    def _generate_order_number(self) -> str:  # Генерация номера заказа вида YYMMDD-xxxxxx
        return datetime.utcnow().strftime("%y%m%d") + "-" + secrets.token_hex(3)  # Дата + случайный hex

    async def list_orders(self, status: str | None = None) -> list[Order]:  # Список заказов (опционально по статусу)
        stmt = select(Order).order_by(Order.created_at.desc())  # Сортируем по дате создания (новые сверху)
        if status:
            stmt = stmt.where(Order.status == status)  # Фильтр по статусу
        res = await self.session.execute(stmt)  # Выполняем запрос
        return list(res.scalars().all())  # Список объектов Order

    async def set_status(self, order_id: int, status: str) -> None:  # Обновить статус заказа
        res = await self.session.execute(select(Order).where(Order.id == order_id))  # Находим заказ по id
        order = res.scalar_one_or_none()  # Заказ или None
        if not order:  # Если не найден — выходим
            return
        order.status = status  # Меняем статус 