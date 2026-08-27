import base64

import cv2
import numpy as np

from app.services.matchers.orb import ORBMatcher, decode_orb_descriptors


def test_orb_decode_binary_base64():
    # 生成随机描述子 (50, 32)
    fake_desc = np.random.randint(0, 256, size=(50, 32), dtype=np.uint8)
    b64_str = base64.b64encode(fake_desc.tobytes()).decode("utf-8")

    decoded = decode_orb_descriptors(b64_str)
    assert decoded is not None
    assert decoded.shape == (50, 32)
    assert np.array_equal(decoded, fake_desc)


def test_orb_matcher_identical_images():
    # 生成一个简单的测试图像
    img = np.zeros((300, 300), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (200, 200), 255, -1)
    cv2.circle(img, (150, 150), 30, 0, -1)

    orb = cv2.ORB.create(nfeatures=200)
    _, desc1 = orb.detectAndCompute(img, None)

    assert desc1 is not None and len(desc1) > 0

    matcher = ORBMatcher()
    score = matcher.compute_score(desc1, desc1)
    assert score >= 0.80  # 完全相同的特征比对得分应显著高于阈值


def test_orb_matcher_different_features():
    desc1 = np.random.randint(0, 50, size=(100, 32), dtype=np.uint8)
    desc2 = np.random.randint(200, 255, size=(100, 32), dtype=np.uint8)

    matcher = ORBMatcher()
    score = matcher.compute_score(desc1, desc2)
    assert score < 0.20  # 毫无关联的特征得分极低
