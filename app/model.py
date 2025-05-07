from pydantic import model_validator, BaseModel
from typing import Optional, List


class CodeInput(BaseModel):
    picture_base64: Optional[str] = None
    phrase_code: Optional[str] = None
    image_code: Optional[List[List[int]]] = None

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


class GetterRequest(CodeInput):
    pass_code: str
