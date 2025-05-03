from app.database import SecretEntry
from tortoise.exceptions import IntegrityError
import json


async def write_db(image_code, words: str, pass_code: str):
    """
    Insert a new record into the database.
    """
    # Serialize image_code (descriptors) to JSON string for storage
    image_code_json = json.dumps(image_code)
    try:
        await SecretEntry.create(
            pass_code=pass_code,
            words=words,
            image_code=image_code_json,
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
    return await SecretEntry.filter(phrase_code__icontains=phrase_code, pass_code=pass_code).first()
