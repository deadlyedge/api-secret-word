import pytest_asyncio
from tortoise import Tortoise


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": ["app.domain.models.secret_entry"]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
