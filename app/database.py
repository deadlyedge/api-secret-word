from tortoise import Tortoise, fields
from tortoise.models import Model
from app.config import DATABASE_URL


DATABASE_URL = DATABASE_URL  # Use the DATABASE_URL from config
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgres://")


class SecretEntry(Model):
    id = fields.IntField(pk=True)
    pass_code = fields.CharField(max_length=255, unique=True)
    words = fields.TextField()
    useImage = fields.BooleanField(default=False)
    phrase_code = fields.CharField(max_length=255, null=True)
    image_code = fields.JSONField()  # Store serialized descriptors as JSON
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "secret_entries"


async def init_db():
    await Tortoise.init(db_url=DATABASE_URL, modules={"models": ["app.database"]})
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()


async def reset_db():
    # Initialize database connection
    await Tortoise.init(db_url=DATABASE_URL, modules={"models": ["app.database"]})
    # Get all user tables
    conn = Tortoise.get_connection("default")
    tables = await conn.execute_query_dict(
        "SELECT tablename FROM pg_tables WHERE schemaname='public';"
    )
    # Drop all tables
    for table in tables:
        table_name = table["tablename"]
        await conn.execute_script(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
    # Recreate tables
    await Tortoise.generate_schemas()
