import pytest_asyncio

from app.services.database import close_db, init_db


@pytest_asyncio.fixture(autouse=True)
async def db_fixture():
    """
    每个测试执行前确保数据库连接就绪；
    测试结束后保留测试写入的数据，直到手动运行 reset_db.py 清理。
    """
    await init_db()
    yield
    await close_db()
