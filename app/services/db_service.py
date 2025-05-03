import json
from app.database import SecretEntry
from tortoise.exceptions import IntegrityError
from typing import Optional


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
    # Serialize image_code (descriptors) to JSON string for storage
    image_code_json = json.dumps(image_code)

    # Validate phrase_code and image_code presence
    if (not phrase_code or phrase_code.strip() == "") and (not image_code or image_code == []):
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
    return await SecretEntry.filter(
        phrase_code__icontains=phrase_code, pass_code=pass_code
    ).first()
