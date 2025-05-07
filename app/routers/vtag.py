from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from urllib.request import urlopen
from json import loads
from app.services.database import find_one_by_pass
from app.services.image_service import get_image_code, match_with_db

router = APIRouter()


@router.post("/vTag")
async def vtag(request: Request):
    data = await request.json()
    pass_code = data.get("passArea")
    picture_url = data.get("picture")

    if not pass_code or not picture_url:
        return JSONResponse(content={"message": "Missing passArea or picture"}, status_code=400)

    read_back = await find_one_by_pass(pass_code)
    if not read_back:
        return JSONResponse(content={"message": "没有这个!PASS"}, status_code=404)

    try:
        read_code = loads(read_back.image_code)
    except Exception:
        return JSONResponse(content={"message": "数据格式错误"}, status_code=500)

    try:
        with urlopen(picture_url) as response:
            picture = response.read()
    except Exception:
        return JSONResponse(content={"message": "Invalid picture URL or unable to fetch"}, status_code=400)

    _, incoming_code = get_image_code(picture)

    if match_with_db(read_code, incoming_code):
        return JSONResponse(content={"words": read_back.words}, status_code=200)
    else:
        return JSONResponse(content={"words": ""}, status_code=200)
