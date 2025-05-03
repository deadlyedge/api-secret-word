from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse
from urllib.request import urlopen
from app.services.image_service import get_image_code
from app.services.db_service import (
    write_db,
    find_one_by_pass,
)
from tortoise.exceptions import IntegrityError

router = APIRouter()


@router.post("/maker")
async def maker(request: Request):
    data = await request.json()
    words = data.get("wordsArea")
    pass_code = data.get("passArea")
    picture_url = data.get("picture")
    phrase_code = data.get("phrase_code")

    if not pass_code:
        raise HTTPException(status_code=400, detail="Missing pass_code")

    existing_entry = await find_one_by_pass(pass_code)
    if existing_entry:
        return JSONResponse(content={"message": "请尝试其他PASS"}, status_code=400)

    image_code = None
    if picture_url:
        try:
            with urlopen(picture_url) as response:
                picture = response.read()
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid picture URL or unable to fetch"
            )

        _, image_code = get_image_code(picture)

    if image_code:
        # Use image_code and pass_code, store words
        try:
            await write_db(
                image_code, words, pass_code, phrase_code=phrase_code, use_image=True
            )
        except IntegrityError:
            return JSONResponse(content={"message": "请尝试其他PASS"}, status_code=400)
    else:
        # No image_code, check phrase_code
        if not phrase_code:
            raise HTTPException(
                status_code=400, detail="Missing phrase_code and image_code"
            )

        try:
            await write_db(
                [], words, pass_code, phrase_code=phrase_code, use_image=False
            )
        except IntegrityError:
            return JSONResponse(content={"message": "请尝试其他PASS"}, status_code=400)

    return JSONResponse(content={"words": words}, status_code=200)
