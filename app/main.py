from fastapi import FastAPI
from app.routers import maker, pass_check, ttag, vtag
from fastapi.responses import JSONResponse
from app.database import init_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化数据库连接和表结构
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(maker.router)
app.include_router(pass_check.router)
app.include_router(vtag.router)
app.include_router(ttag.router)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"}, status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
