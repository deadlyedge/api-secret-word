from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from app.services.database import find_one_by_pass

router = APIRouter()


@router.post("/passCheck")
async def pass_check(request: Request):
    data = await request.json()
    pass_code = data.get("passCode")
    if not pass_code:
        return JSONResponse(content={"message": "Missing passCode"}, status_code=400)

    read_back = find_one_by_pass(pass_code)
    if read_back:
        return JSONResponse(content={"message": "PASS unavailable"}, status_code=200)
    else:
        return JSONResponse(content={"message": ""}, status_code=200)
