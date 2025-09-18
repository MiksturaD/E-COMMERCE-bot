from __future__ import annotations  # Отложенная оценка аннотаций

from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, UniqueConstraint  # Типы и связи
from sqlalchemy.orm import Mapped, mapped_column, relationship  # Описание ORM полей и связей
from datetime import datetime  # Метка времени создания

from .database import Base  # Базовый класс ORM

class User(Base):  # Пользователь бота
    __tablename__ = "users"  # Таблица users
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # PK
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)  # Telegram ID пользователя (уникальный)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Имя
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Телефон
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)  # Адрес
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Дата создания

    cart_items: Mapped[list[CartItem]] = relationship(back_populates="user", cascade="all, delete-orphan")  # Связь с корзиной
    orders: Mapped[list[Order]] = relationship(back_populates="user", cascade="all, delete-orphan")  # Связь с заказами

class Category(Base):  # Категория товаров
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # PK
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)  # Название категории (уникально)

    products: Mapped[list[Product]] = relationship(back_populates="category")  # Список товаров в категории

class Product(Base):  # Товар
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # PK
    title: Mapped[str] = mapped_column(String(255), index=True)  # Название товара
    description: Mapped[str] = mapped_column(String(2048))  # Описание
    price_cents: Mapped[int] = mapped_column(Integer)  # Цена в копейках
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)  # URL фото
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Активен ли товар

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)  # FK на категорию
    category: Mapped[Category | None] = relationship(back_populates="products")  # Объект категории

class CartItem(Base):  # Позиция в корзине
    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # PK

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))  # FK на пользователя
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))  # FK на товар
    quantity: Mapped[int] = mapped_column(Integer, default=1)  # Количество товара

    user: Mapped[User] = relationship(back_populates="cart_items")  # Объект пользователя
    product: Mapped[Product] = relationship()  # Объект товара

    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)  # Уникальность пары (user, product)

class Order(Base):  # Заказ
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # PK
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # FK на пользователя (может быть NULL)
    total_cents: Mapped[int] = mapped_column(Integer)  # Итоговая сумма в копейках
    delivery_method: Mapped[str] = mapped_column(String(64))  # Способ доставки
    status: Mapped[str] = mapped_column(String(32), default="new")  # Статус заказа
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)  # Дата создания

    customer_name: Mapped[str] = mapped_column(String(255))  # Имя клиента
    customer_phone: Mapped[str] = mapped_column(String(32))  # Телефон клиента
    customer_address: Mapped[str] = mapped_column(String(512))  # Адрес клиента
    order_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)  # Внешний номер заказа

    user: Mapped[User | None] = relationship(back_populates="orders")  # Объект пользователя
    items: Mapped[list[OrderItem]] = relationship(back_populates="order", cascade="all, delete-orphan")  # Позиции заказа

class OrderItem(Base):  # Позиция заказа
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # PK

    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))  # FK на заказ
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)  # FK на товар (может быть NULL)
    quantity: Mapped[int] = mapped_column(Integer, default=1)  # Количество
    price_cents: Mapped[int] = mapped_column(Integer)  # Цена на момент заказа (в копейках)

    order: Mapped[Order] = relationship(back_populates="items")  # Объект заказа
    product: Mapped[Product | None] = relationship()  # Объект товара (может отсутствовать) 