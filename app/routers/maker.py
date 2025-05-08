from fastapi import APIRouter
import asyncio
from tortoise.exceptions import IntegrityError

from app.model import MakerRequest
from app.services.image_service import get_image_code
from app.services.database import (
    write_db,
    find_one_by_pass,
)
from app.utils.response import (
    json_response,
    error_response,
    validation_error_response,
)

router = APIRouter()


@router.post("/maker")
async def maker(request_data: MakerRequest):
    existing_entry = await find_one_by_pass(request_data.pass_code)
    if existing_entry:
        return error_response("请尝试其他PASS", http_status=400)

    image_code = request_data.image_code
    if request_data.picture_base64 and not image_code:
        try:
            loop = asyncio.get_running_loop()
            _, image_code = await loop.run_in_executor(
                None, get_image_code, request_data.picture_base64
            )
        except Exception:
            return validation_error_response("Invalid base64 picture data or unable to process")

    use_image = bool(image_code and image_code != [])

    try:
        await write_db(
            image_code if use_image else None,
            request_data.words,
            request_data.pass_code,
            phrase_code=request_data.phrase_code,
            use_image=use_image,
        )
    except IntegrityError:
        return error_response("请尝试其他PASS", http_status=400)

    return json_response(
        data={"words": request_data.words, "pass_code": request_data.pass_code},
        http_status=200,
    )
