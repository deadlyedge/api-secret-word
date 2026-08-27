import logging

from app.domain.models.secret_entry import SecretEntry
from app.domain.schemas.evidence import MatchItem, VerifyRequest, VerifyResponse
from app.services.database import find_candidates_by_credential, update_viewed_at
from app.services.matchers.orb import ORBMatcher, decode_orb_descriptors

logger = logging.getLogger(__name__)


class MatchEngine:
    """
    视觉凭证与特征比对决策引擎
    负责：
    1. 根据 credential_value 检索所有候选库记录（一对多）
    2. 反序列化描述子并执行 OpenCV ORB 高精度匹配
    3. 过滤低于阈值 (min_score) 的条目
    4. 降序排列并截取 Top-5 返回
    """

    def __init__(self, default_min_score: float = 0.60):
        self.default_min_score = default_min_score
        self.orb_matcher = ORBMatcher(ratio_threshold=0.75)

    def _match_sync(
        self,
        query_feature_data: str,
        candidates: list[SecretEntry],
        min_score: float,
    ) -> list[MatchItem]:
        """
        同步执行 CPU 密集的描述子解码与矩阵 KNN 比对
        """
        query_desc = decode_orb_descriptors(query_feature_data)
        if query_desc is None:
            logger.warning("Query ORB descriptors could not be decoded.")
            return []

        matched_items: list[MatchItem] = []

        for cand in candidates:
            cand_desc = decode_orb_descriptors(cand.feature_data)
            if cand_desc is None:
                continue

            score = self.orb_matcher.compute_score(query_desc, cand_desc)
            logger.debug(
                f"Candidate ID {cand.id} match score: {score:.4f} (threshold: {min_score})"
            )

            if score >= min_score:
                matched_items.append(
                    MatchItem(
                        id=cand.id,
                        score=round(score, 4),
                        secret_text=cand.secret_text,
                        created_at=cand.created_at,
                    )
                )

        # 按 score 从高到低降序排序
        matched_items.sort(key=lambda item: item.score, reverse=True)
        # 截取 Top-5
        return matched_items[:5]

    async def verify(self, request: VerifyRequest) -> VerifyResponse:
        """
        执行完整的检索与比对判定流程
        """
        credential_value = request.evidence.credential_value
        min_score = (
            request.min_score
            if request.min_score is not None
            else self.default_min_score
        )

        # 1. 查询数据库中符合该 passcode 的所有候选记录（可能存在多条）
        candidates = await find_candidates_by_credential(credential_value)
        if not candidates:
            return VerifyResponse(
                matched=False,
                count=0,
                results=[],
                message=f"未能找到凭证为 '{credential_value}' 的任何候选记录",
            )

        # 2. 特征比对与排序截取 (Top-5)
        top_matches = self._match_sync(
            query_feature_data=request.evidence.feature_data,
            candidates=candidates,
            min_score=min_score,
        )

        if not top_matches:
            return VerifyResponse(
                matched=False,
                count=0,
                results=[],
                message="找到了凭证对应的候选库，但图像特征未能达到有效匹配阈值",
            )

        # 3. 异步更新命中记录的 viewed_at 时间戳
        hit_ids = [item.id for item in top_matches]
        try:
            await update_viewed_at(hit_ids)
        except Exception:
            logger.exception("Failed to update viewed_at for entries %s", hit_ids)

        return VerifyResponse(
            matched=True,
            count=len(top_matches),
            results=top_matches,
            message=f"成功匹配到 {len(top_matches)} 条符合要求的密语记录",
        )


# 全局单例引擎
match_engine = MatchEngine()
