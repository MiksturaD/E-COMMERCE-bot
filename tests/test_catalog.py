import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from bot.models import Category, Product
from bot.services.catalog_service import CatalogService
from bot.keyboards import PAGE_SIZE
from bot.database import Base

@pytest.mark.asyncio
async def test_list_categories_and_products(tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with Session() as session:
        c1 = Category(name="A")
        c2 = Category(name="B")
        session.add_all([c1, c2])
        await session.flush()
        for i in range(PAGE_SIZE + 2):
            session.add(Product(title=f"P{i}", description="D", price_cents=100, category_id=c1.id, is_active=True))
        await session.commit()

    async with Session() as session:
        service = CatalogService(session)
        cats = await service.list_categories()
        assert len(cats) == 2
        products, total_pages = await service.list_products(c1.id, page=1)
        assert len(products) == PAGE_SIZE
        assert total_pages == 2 