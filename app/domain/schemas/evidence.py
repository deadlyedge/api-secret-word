from datetime import datetime

from pydantic import BaseModel, Field

AlgorithmType = str
CredentialType = str


class VisualEvidence(BaseModel):
    credential_type: CredentialType = Field(
        default="qr", description="凭证类型 (qr/barcode/ocr/composite)"
    )
    credential_value: str = Field(..., description="识别出的凭证值/passcode")
    algorithm: AlgorithmType = Field(default="orb", description="核心特征提取算法")
    feature_data: str = Field(..., description="Base64 编码的描述子二进制矩阵或哈希值")
    keypoints_count: int | None = Field(None, description="关键点数量")
    width: int = Field(default=640, description="标准化宽度")
    height: int = Field(default=480, description="标准化高度")
    extra_features: dict[str, str] | None = Field(None, description="可选辅助哈希特征")


class VerifyRequest(BaseModel):
    evidence: VisualEvidence = Field(..., description="前端预处理并提取的凭证与特征")
    min_score: float | None = Field(
        default=0.60, description="最低有效匹配阈值 (0.0~1.0)"
    )


class MatchItem(BaseModel):
    id: int = Field(..., description="密语记录 ID")
    title: str | None = Field(None, description="密语标题/描述")
    score: float = Field(..., description="匹配相似度得分 (0.0~1.0)")
    secret_text: str | None = Field(None, description="关联的解密内容")
    created_at: datetime = Field(..., description="创建时间")


class VerifyResponse(BaseModel):
    matched: bool = Field(..., description="是否存在达标匹配项")
    count: int = Field(..., description="命中数量 (<= 5)")
    results: list[MatchItem] = Field(
        default_factory=list, description="匹配度高于阈值的前五结果（按 score 降序）"
    )
    message: str = Field(..., description="结果描述信息")


class SecretCreateRequest(BaseModel):
    title: str | None = Field(None, description="密语标题/备注")
    secret_text: str = Field(..., description="密语内容")
    evidence: VisualEvidence = Field(..., description="绑定的凭证与特征")
