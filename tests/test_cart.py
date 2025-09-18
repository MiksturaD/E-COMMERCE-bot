import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from bot.database import Base
from bot.models import Product
from bot.services.cart_service import CartService

@pytest.mark.asyncio
async def test_add_and_change_cart():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with Session() as session:
        session.add(Product(title="T", description="D", price_cents=2500, is_active=True))
        await session.commit()

    async with Session() as session:
        cart = CartService(session)
        user = await cart.ensure_user(1)
        await cart.add_to_cart(user, 1, 1)
        await cart.change_qty(user, 1, 2)
        await session.commit()

    async with Session() as session:
        cart = CartService(session)
        user = await cart.ensure_user(1)
        items = await cart.get_cart(user)
        assert items[0][1] == 3
        assert cart.calculate_total(items) == 7500 