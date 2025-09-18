from __future__ import annotations  # Отложенная оценка аннотаций

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker  # Асинхронный движок и фабрика сессий
from sqlalchemy.orm import DeclarativeBase  # Базовый класс ORM моделей
from sqlalchemy import select  # Конструктор SELECT-запросов

from .config import settings  # Настройки приложения
from .logger import logger  # Логгер

class Base(DeclarativeBase):  # Базовый класс для всех ORM моделей
    pass  # Содержит общую метадату

engine = create_async_engine(settings.database_url, echo=False, future=True)  # Создаём асинхронный движок БД
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # Фабрика асинхронных сессий

async def init_models() -> None:  # Создание таблиц при старте
    from . import models  # noqa: F401  # Импорт моделей, чтобы они были зарегистрированы в метадате
    async with engine.begin() as conn:  # Открываем транзакцию на подключении
        await conn.run_sync(Base.metadata.create_all)  # Создаём таблицы, если отсутствуют
    logger.info("Database initialized")  # Пишем в лог об инициализации

async def get_one(session: AsyncSession, stmt):  # Вспомогательная функция: получить одну запись или None
    result = await session.execute(stmt)  # Выполняем запрос
    return result.scalar_one_or_none()  # Возвращаем одну запись или None

async def get_all(session: AsyncSession, stmt):  # Вспомогательная функция: получить список записей
    result = await session.execute(stmt)  # Выполняем запрос
    return result.scalars().all()  # Возвращаем все результаты как список 