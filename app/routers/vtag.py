from fastapi import APIRouter
import numpy as np
from app.model import GetterRequest
from app.services.database import find_one_by_pass, update_viewed_at
from app.services.image_service import deserialize_code, match_with_db
import asyncio
from app.utils.response import (
    json_response,
    error_response,
    not_found_response,
    validation_error_response,
)

router = APIRouter()


@router.post("/vTag")
async def vtag(request_data: GetterRequest):
    if not request_data.pass_code or not request_data.image_code:
        return validation_error_response("Missing passArea or picture")

    read_back = await find_one_by_pass(request_data.pass_code)
    if not read_back:
        return not_found_response("没有这个!PASS")

    try:
        read_code = np.asarray(deserialize_code(read_back.image_code))
        incoming_code = np.asarray(request_data.image_code)
    except Exception as e:
        return error_response(f"数据格式错误: {str(e)}", http_status=500)

    loop = asyncio.get_running_loop()
    matched = await loop.run_in_executor(None, match_with_db, read_code, incoming_code)

    if matched:
        print(f"{request_data.pass_code} matched! and the words are {read_back.words}")
        await update_viewed_at(request_data.pass_code)
        return json_response(data={"words": read_back.words})
    else:
        return validation_error_response("NOT FOUND")
