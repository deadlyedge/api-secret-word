import base64

import cv2
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient

from app.domain.schemas.evidence import (
    SecretCreateRequest,
    VerifyRequest,
    VisualEvidence,
)
from app.main import app


def _generate_test_descriptors(pattern_type: int) -> str:
    """生成带有不同几何图案的图像并提取 ORB 描述子 Base64"""
    img = np.zeros((300, 300), dtype=np.uint8)
    if pattern_type == 1:
        cv2.rectangle(img, (30, 30), (120, 120), 255, -1)
        cv2.circle(img, (200, 200), 45, 255, -1)
    elif pattern_type == 2:
        cv2.circle(img, (150, 150), 80, 255, 3)
        cv2.line(img, (0, 0), (300, 300), 255, 2)
    elif pattern_type == 3:
        cv2.rectangle(img, (80, 80), (250, 250), 255, 2)
        cv2.putText(img, "TEST", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 2, 255, 3)
    else:
        cv2.circle(img, (100, 100), 20, 255, -1)

    orb = cv2.ORB.create(nfeatures=300)
    _, desc = orb.detectAndCompute(img, None)
    if desc is None:
        desc = np.random.randint(0, 256, size=(50, 32), dtype=np.uint8)
    return base64.b64encode(desc.tobytes()).decode("utf-8")


@pytest.mark.asyncio
async def test_one_to_many_secrets_and_top5_verification():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. 测试健康检查
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # 2. 模拟针对同一个 passcode="Eiffel_Tower_123" 录入 3 条不同图片特征的密语（一对多）
        passcode = "Eiffel_Tower_123"
        desc_pattern1 = _generate_test_descriptors(1)
        desc_pattern2 = _generate_test_descriptors(2)
        desc_pattern3 = _generate_test_descriptors(3)

        # 录入第 1 条密语
        req1 = SecretCreateRequest(
            secret_text="明天下午三点老地方见",
            evidence=VisualEvidence(
                credential_type="qr",
                credential_value=passcode,
                algorithm="orb",
                feature_data=desc_pattern1,
                width=300,
                height=300,
            ),
        )
        res1 = await client.post("/api/v1/secrets", json=req1.model_dump())
        assert res1.status_code == 201, f"Error: {res1.text}"
        data1 = res1.json()
        assert data1["credential_value"] == passcode
        assert "id" in data1  # UUIDv7 字符串

        # 录入第 2 条密语
        req2 = SecretCreateRequest(
            secret_text="钥匙在花盆底下",
            evidence=VisualEvidence(
                credential_type="qr",
                credential_value=passcode,
                algorithm="orb",
                feature_data=desc_pattern2,
                width=300,
                height=300,
            ),
        )
        res2 = await client.post("/api/v1/secrets", json=req2.model_dump())
        assert res2.status_code == 201, f"Error: {res2.text}"

        # 录入第 3 条密语
        req3 = SecretCreateRequest(
            secret_text="会议室代码 8899",
            evidence=VisualEvidence(
                credential_type="qr",
                credential_value=passcode,
                algorithm="orb",
                feature_data=desc_pattern3,
                width=300,
                height=300,
            ),
        )
        res3 = await client.post("/api/v1/secrets", json=req3.model_dump())
        assert res3.status_code == 201, f"Error: {res3.text}"

        # 3. 验证：持 pattern 1 特征进行比对检索
        verify_req1 = VerifyRequest(
            evidence=VisualEvidence(
                credential_type="qr",
                credential_value=passcode,
                algorithm="orb",
                feature_data=desc_pattern1,
                width=300,
                height=300,
            ),
            min_score=0.60,
        )
        v_res1 = await client.post("/api/v1/verify", json=verify_req1.model_dump())
        assert v_res1.status_code == 200, f"Error: {v_res1.text}"
        v_data1 = v_res1.json()
        assert v_data1["matched"] is True
        assert v_data1["count"] >= 1
        # 最佳匹配项 (Top-1) 应是“老地方见”
        assert v_data1["results"][0]["secret_text"] == "明天下午三点老地方见"
        assert v_data1["results"][0]["score"] >= 0.70
        assert "id" in v_data1["results"][0]  # 匹配项中包含 UUIDv7 ID

        # 4. 验证：不存在的 passcode
        verify_req_none = VerifyRequest(
            evidence=VisualEvidence(
                credential_type="qr",
                credential_value="Non_Existent_Passcode",
                algorithm="orb",
                feature_data=desc_pattern1,
                width=300,
                height=300,
            ),
            min_score=0.60,
        )
        v_res_none = await client.post(
            "/api/v1/verify", json=verify_req_none.model_dump()
        )
        assert v_res_none.status_code == 200, f"Error: {v_res_none.text}"
        assert v_res_none.json()["matched"] is False
        assert v_res_none.json()["count"] == 0
        assert len(v_res_none.json()["results"]) == 0
