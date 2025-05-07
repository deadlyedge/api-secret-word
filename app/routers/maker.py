from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from tortoise.exceptions import IntegrityError

from app.model import MakerRequest
from app.services.image_service import get_image_code
from app.services.database import (
    write_db,
    find_one_by_pass,
)

router = APIRouter()


@router.post("/maker")
async def maker(request_data: MakerRequest):
    print(request_data)
    existing_entry = await find_one_by_pass(request_data.pass_code)
    if existing_entry:
        return JSONResponse(content={"message": "请尝试其他PASS"}, status_code=400)

    image_code = request_data.image_code
    if request_data.picture_base64 and not image_code:
        try:
            _, image_code = get_image_code(request_data.picture_base64)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid base64 picture data or unable to process",
            )

    try:
        if image_code:
            await write_db(
                image_code,
                request_data.words,
                request_data.pass_code,
                phrase_code=request_data.phrase_code,
                use_image=True,
            )
        else:
            await write_db(
                [],
                request_data.words,
                request_data.pass_code,
                phrase_code=request_data.phrase_code,
                use_image=False,
            )
    except IntegrityError:
        return JSONResponse(content={"message": "请尝试其他PASS"}, status_code=400)

    return JSONResponse(
        content={"words": request_data.words, "pass_code": request_data.pass_code},
        status_code=200,
    )
