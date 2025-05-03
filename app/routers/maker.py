from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse
from urllib.request import urlopen
from app.services.image_service import get_image_code
from app.services.db_service import write_db, find_one_by_phrase_and_pass
from tortoise.exceptions import IntegrityError

router = APIRouter()


@router.post("/maker")
async def maker(request: Request):
    data = await request.json()
    words = data.get("wordsArea")
    pass_code = data.get("passArea")
    picture_url = data.get("picture")
    phrase_code = data.get("phrase_code")

    if not all([pass_code, picture_url]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    if phrase_code:
        # Use phrase_code and pass_code to find matching words with fuzzy matching
        record = await find_one_by_phrase_and_pass(phrase_code, pass_code)
        if record:
            return JSONResponse(content={"words": record.words}, status_code=200)
        else:
            raise HTTPException(status_code=400, detail="No matching record found for phrase_code and pass_code")

    if not words:
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        with urlopen(picture_url) as response:
            picture = response.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid picture URL or unable to fetch")

    _, image_code = get_image_code(picture)

    try:
        await write_db(image_code, words, pass_code)
    except IntegrityError:
        return JSONResponse(content={"message": "请尝试其他PASS"}, status_code=400)

    return JSONResponse(content={"words": words}, status_code=200)
