from fastapi import APIRouter, Request, HTTPException
from starlette.responses import JSONResponse
from app.services.db_service import (
    find_one_by_phrase_and_pass,
)

router = APIRouter()


@router.post("/tTag")
async def tTag(request: Request):
    data = await request.json()
    pass_code = data.get("passArea")
    phrase_code = data.get("phrase_code")

    if not pass_code or not phrase_code:
        raise HTTPException(status_code=400, detail="Missing pass_code or phrase_code")

    record = await find_one_by_phrase_and_pass(phrase_code, pass_code)
    if record:
        return JSONResponse(content={"words": record.words}, status_code=200)
    else:
        raise HTTPException(
            status_code=404,
            detail="No matching record found for phrase_code and pass_code",
        )
