from pydantic import BaseModel


class StandardResponse[T](BaseModel):
    success: bool = True
    code: str = "OK"
    message: str = "Success"
    data: T | None = None
