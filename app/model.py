from datetime import datetime

from pydantic import BaseModel, model_validator


class CodeInput(BaseModel):
    picture_base64: str | None = None
    phrase_code: str | None = None
    image_code: list[list[int]] | None = None

    @model_validator(mode="before")
    def check_exclusive_fields(cls, values):
        picture_base64, phrase_code, image_code = (
            values.get("picture_base64"),
            values.get("phrase_code"),
            values.get("image_code"),
        )
        count = sum(x is not None for x in [picture_base64, phrase_code, image_code])
        if count != 1:
            raise ValueError(
                "picture_base64, phrase_code, and image_code must have exactly one provided"
            )
        return values


class MakerRequest(CodeInput):
    words: str
    pass_code: str
    owner: str | None = "guest"


class GetterRequest(CodeInput):
    pass_code: str


class SecretEntryModel(BaseModel):
    id: int
    pass_code: str
    words: str
    useImage: bool = False
    phrase_code: str | None = None
    image_code: bytes | None = None
    created_at: datetime
    viewed_at: datetime | None = None
    owner: str | None = "guest"

    class Config:
        from_attributes = True
