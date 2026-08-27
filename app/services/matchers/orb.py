import base64
import json
import zlib

import cv2
import numpy as np

from app.services.matchers.base import BaseMatcher


def decode_orb_descriptors(feature_data: str | bytes) -> np.ndarray | None:
    """
    将前端传入的特征数据还原为 NumPy (N, 32) uint8 描述子矩阵。
    支持以下几种常见格式：
    1. 纯 Base64 编码的 bytes (Uint8Array 二进制字节流，N * 32 字节)
    2. JSON 数组序列化后的 Base64 / 字符串 / 压缩包 (兼容历史格式)
    """
    if feature_data is None:
        return None

    if isinstance(feature_data, str):
        try:
            raw_bytes = base64.b64decode(feature_data)
        except (ValueError, TypeError):
            raw_bytes = feature_data.encode("utf-8")
    else:
        raw_bytes = feature_data

    # 尝试 zlib 解压（如果之前做了压缩）
    try:
        decompressed = zlib.decompress(raw_bytes)
    except zlib.error:
        decompressed = raw_bytes

    # 情况 A: 解压后是 JSON 格式（如 [[...], [...]] 或数字列表）
    try:
        data = json.loads(decompressed.decode("utf-8"))
        arr = np.array(data, dtype=np.uint8)
        if arr.ndim == 2 and arr.shape[1] == 32:
            return arr
        if arr.size % 32 == 0 and arr.size > 0:
            return arr.reshape(-1, 32)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        pass

    # 情况 B: 二进制 Uint8Array 描述子流 (每个 ORB 描述子 32 字节)
    if len(decompressed) % 32 == 0 and len(decompressed) > 0:
        arr = np.frombuffer(decompressed, dtype=np.uint8).reshape(-1, 32)
        return arr

    return None


class ORBMatcher(BaseMatcher):
    """
    基于 OpenCV BFMatcher (NORM_HAMMING) 与 Lowe's ratio test 的高精度 ORB 局部特征匹配器
    """

    def __init__(self, ratio_threshold: float = 0.75, nfeatures: int = 500):
        self.ratio_threshold = ratio_threshold
        self.nfeatures = nfeatures
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    def compute_score(
        self, query_feature: np.ndarray | None, candidate_feature: np.ndarray | None
    ) -> float:
        """
        比对两个描述子矩阵并计算相似度评分 (0.0 ~ 1.0)。
        评分基于 Lowe's ratio test 筛选出的良好匹配点 (Good Matches) 占查询描述子总数的比例。
        """
        if query_feature is None or candidate_feature is None:
            return 0.0

        if query_feature.size == 0 or candidate_feature.size == 0:
            return 0.0

        # KNN 比对要求候选特征库至少有 2 个关键点
        if len(candidate_feature) < 2 or len(query_feature) < 2:
            try:
                matches = self.bf.match(query_feature, candidate_feature)
                if not matches:
                    return 0.0
                good_matches = [m for m in matches if m.distance < 50.0]
                return float(len(good_matches) / max(len(query_feature), 1))
            except cv2.error:
                return 0.0

        try:
            matches = self.bf.knnMatch(query_feature, candidate_feature, k=2)
        except cv2.error:
            return 0.0

        good_matches = []
        for m_n in matches:
            if len(m_n) == 2:
                m, n = m_n
                if m.distance < self.ratio_threshold * n.distance:
                    good_matches.append(m)

        if len(matches) == 0:
            return 0.0

        # 相似度打分：Good matches 数量与查询关键点数量比值 (上限 1.0)
        score = len(good_matches) / len(query_feature)
        return float(min(score, 1.0))
