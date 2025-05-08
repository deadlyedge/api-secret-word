import json
import zlib
from datetime import datetime
from typing import Optional

from tortoise import Tortoise, fields
from tortoise.models import Model
from tortoise.exceptions import IntegrityError

from app.config import DATABASE_URL


class SecretEntry(Model):
    id = fields.IntField(pk=True)
    pass_code = fields.CharField(max_length=255, unique=True)
    words = fields.TextField()
    useImage = fields.BooleanField(default=False)
    phrase_code = fields.CharField(max_length=255, null=True)
    image_code = fields.BinaryField(
        null=True
    )  # Store compressed serialized descriptors as binary, allow null
    created_at = fields.DatetimeField(auto_now_add=True)
    viewed_at = fields.DatetimeField(null=True)
    owner = fields.CharField(default="guest", max_length=255, null=True)

    class Meta:
        table = "secret_entries"


async def init_db():
    await Tortoise.init(
        db_url=DATABASE_URL, modules={"models": ["app.services.database"]}
    )
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()


async def reset_db():
    # Initialize database connection
    await Tortoise.init(
        db_url=DATABASE_URL, modules={"models": ["app.services.database"]}
    )
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


async def write_db(
    image_code,
    words: str,
    pass_code: str,
    phrase_code: Optional[str] = None,
    use_image: bool = True,
):
    """
    Insert a new record into the database.
    """
    # Serialize image_code (descriptors) to JSON string, encode and compress for storage
    raw = json.dumps(image_code).encode("utf-8")
    compressed = zlib.compress(raw)

    # Validate phrase_code and image_code presence
    if (not phrase_code or phrase_code.strip() == "") and (
        not image_code or image_code == []
    ):
        raise ValueError("Either phrase_code or image_code must be provided")

    # If image_code is provided and not empty, set useImage to True
    if image_code and image_code != []:
        use_image = True

    try:
        await SecretEntry.create(
            pass_code=pass_code,
            words=words,
            phrase_code=phrase_code,
            useImage=use_image,
            image_code=compressed,
        )
    except IntegrityError:
        raise


async def find_one_by_pass(pass_code: str):
    """
    Find one record by pass_code.
    """
    return await SecretEntry.filter(pass_code=pass_code).first()


async def find_one_by_phrase_and_pass(phrase_code: str, pass_code: str):
    """
    Find one record by fuzzy matching phrase_code and exact pass_code.
    """
    return await SecretEntry.filter(
        phrase_code__icontains=phrase_code, pass_code=pass_code
    ).first()


async def update_viewed_at(pass_code: str):
    """
    Update the viewed_at timestamp for a given pass_code.
    """
    await SecretEntry.filter(pass_code=pass_code).update(viewed_at=datetime.now())
