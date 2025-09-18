import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from bot.database import Base
from bot.models import Product
from bot.services.cart_service import CartService
from bot.services.order_service import OrderService

@pytest.mark.asyncio
async def test_create_order_clears_cart_and_generates_number():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with Session() as session:
        session.add(Product(title="X", description="D", price_cents=1234, is_active=True))
        await session.commit()

    async with Session() as session:
        cart = CartService(session)
        user = await cart.ensure_user(42)
        await cart.add_to_cart(user, 1, 2)
        await session.commit()

    async with Session() as session:
        order_service = OrderService(session)
        cart = CartService(session)
        user = await cart.ensure_user(42)
        order = await order_service.create_order(user, "Name", "+123456789", "Addr", "Курьер")
        await session.commit()
        assert order.order_number

    async with Session() as session:
        cart = CartService(session)
        user = await cart.ensure_user(42)
        items = await cart.get_cart(user)
        assert items == [] 