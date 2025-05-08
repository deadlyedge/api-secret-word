from fastapi import APIRouter
import numpy as np
from starlette.responses import JSONResponse
from app.model import GetterRequest
from app.services.database import find_one_by_pass
from app.services.image_service import match_with_db
import asyncio

router = APIRouter()


@router.post("/vTag")
async def vtag(request_data: GetterRequest):
    if not request_data.pass_code or not request_data.image_code:
        return JSONResponse(
            content={"message": "Missing passArea or picture"}, status_code=400
        )

    read_back = await find_one_by_pass(request_data.pass_code)
    if not read_back:
        return JSONResponse(content={"message": "没有这个!PASS"}, status_code=404)

    try:
        read_code = np.asarray(read_back.image_code)
        incoming_code = np.asarray(request_data.image_code)
    except Exception as e:
        return JSONResponse(
            content={"message": "数据格式错误", "error": str(e)}, status_code=500
        )

    # process image in backend
    # try:
    #     with urlopen(picture_url) as response:
    #         picture = response.read()
    # except Exception:
    #     return JSONResponse(content={"message": "Invalid picture URL or unable to fetch"}, status_code=400)

    # _, incoming_code = get_image_code(picture)

    loop = asyncio.get_running_loop()
    matched = await loop.run_in_executor(
        None, match_with_db, read_code, incoming_code
    )

    if matched:
        print(f"{request_data.pass_code} matched! and the words are {read_back.words}")
        return JSONResponse(content={"words": read_back.words}, status_code=200)
    else:
        return JSONResponse(content={"words": "NOT FOUND"}, status_code=201)
