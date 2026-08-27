from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.domain.schemas.evidence import SecretCreateRequest
from app.services.database import create_secret_entry

router = APIRouter(tags=["Secrets"])


class SecretCreateResponse(BaseModel):
    id: UUID
    credential_value: str
    message: str


@router.post(
    "/secrets",
    response_model=SecretCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="录入新密语与视觉特征",
)
async def create_secret(request: SecretCreateRequest) -> SecretCreateResponse:
    """
    录入一条新的密语并绑定对应的凭证（passcode）与图像特征描述子。
    主键自动生成标准 UUIDv7，支持同一个 passcode 绑定多个不同的视觉形象及密语内容（一对多）。
    """
    try:
        entry = await create_secret_entry(
            secret_text=request.secret_text,
            evidence=request.evidence,
        )
        return SecretCreateResponse(
            id=entry.id,
            credential_value=entry.credential_value,
            message="密语与视觉特征已成功录入",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"录入密语失败: {e!s}",
        ) from e
