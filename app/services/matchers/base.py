from abc import ABC, abstractmethod
from typing import Any


class BaseMatcher(ABC):
    """
    匹配器策略抽象基类
    """

    @abstractmethod
    def compute_score(self, query_feature: Any, candidate_feature: Any) -> float:
        """
        计算查询特征与候选特征之间的相似度评分 (0.0 ~ 1.0)
        """
