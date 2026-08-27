from fastapi import APIRouter

from app.domain.schemas.evidence import VerifyRequest, VerifyResponse
from app.services.match_engine import match_engine

router = APIRouter(tags=["Verification"])


@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="验证视觉凭证并获取匹配密语 (Top-5)",
)
async def verify_evidence(request: VerifyRequest) -> VerifyResponse:
    """
    根据前端发来的凭证 (passcode / credential_value) 和 ORB 特征描述子：
    1. 在数据库中检索所有符合该凭证的候选特征库（支持一对多）；
    2. 比对各候选特征，计算相似度得分；
    3. 过滤低于阈值项，按得分降序返回前 5 个匹配结果及解密密语。
    """
    return await match_engine.verify(request)
