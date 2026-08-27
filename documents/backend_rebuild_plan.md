# Backend 重构实施计划 (Backend Rebuild Plan)

本文档专注于 **后端系统 (Backend)** 的具体重构与落地实施，严格基于 `documents/重构工作计划.md`、`documents/重构实施方案 v3.md` (v3.1) 以及 `AGENTS.md` 制定。

---

## 1. 重构背景与后端核心目标

### 1.1 业务核心逻辑
- **凭证驱动与一对多检索**：前端预先提取 `passcode`（`credential_value`）及标准化 ORB 描述子特征。后端根据 `passcode` 从数据库中检索出**所有符合该凭证的候选记录（支持一对多，单个 passcode 可对应多个已存密语与特征）**。
- **高精度比对与 Top-5 决策**：后端利用 OpenCV-Python（KNN + Lowe's ratio test）对所有候选特征逐一精配，计算相似度评分（`score`，0.0~1.0），过滤低于阈值（如 `min_score = 0.60`）的条目，按得分降序排序，最终**返回高于阈值的前 5 个结果（Top-5）**及对应的解密密语。

### 1.2 现有代码问题与重构范围
1. **命名混乱与契约不一致**：历史代码中存在 `pass_code`、`phrase_code`、`image_code`、`passArea` 等混合命名。
2. **一对一强约束需解除**：`SecretEntry.pass_code` 原设置了 `unique=True`，需改为非唯一索引 `index=True` 以支持一对多业务场景。
3. **算法耦合度高**：比对逻辑散落在 `image_service.py` 和路由中，需封装为策略模式（`matchers/`）与独立的决策引擎（`MatchEngine`）。
4. **异步与线程池**：CPU 密集的矩阵比对需通过 `run_in_threadpool` 包装，防止阻塞 FastAPI 主事件循环。

---

## 2. 目标架构与模块目录设计

重构后的后端代码结构如下：

```text
app/
├── config.py                     # 全局配置 (DATABASE_URL, 默认阈值等)
├── main.py                       # FastAPI 入口、生命周期与全局中间件/异常捕获
├── domain/                       # 领域层 (模型与契约)
│   ├── models/
│   │   ├── __init__.py
│   │   └── secret_entry.py       # Tortoise ORM 实体 (支持 credential_value 一对多索引)
│   └── schemas/
│       ├── __init__.py
│       ├── common.py             # 通用返回结构 (StandardResponse 等)
│       └── evidence.py           # 核心契约 (VisualEvidence, VerifyRequest, VerifyResponse, MatchItem, SecretCreateRequest)
├── services/                     # 业务与计算服务层
│   ├── __init__.py
│   ├── database.py               # 数据库初始化与 CRUD (find_candidates_by_credential 等)
│   ├── match_engine.py           # Top-5 匹配决策引擎
│   └── matchers/                 # 算法策略实现
│       ├── __init__.py
│       ├── base.py               # BaseMatcher 抽象基类
│       ├── orb.py                # ORB 特征反序列化与 KNN 匹配实现
│       └── hash.py               # (可选扩展) 汉明距离哈希比对器
├── routers/                      # API 路由层 (v1)
│   ├── __init__.py
│   ├── api_v1.py                 # API v1 统一路由聚合
│   ├── verify.py                 # POST /api/v1/verify (验证与比对)
│   ├── secrets.py                # POST /api/v1/secrets (录入新密语)
│   └── health.py                 # GET /health
└── utils/                        # 工具模块
    ├── __init__.py
    └── response.py               # 响应工具函数
```

---

## 3. 详细实施步骤 (Step-by-Step Implementation)

### 步骤 1：定义统一的 Pydantic 数据契约 (`app/domain/schemas/`)

- **文件**：`app/domain/schemas/evidence.py`
- **内容**：
  - `AlgorithmType = Literal["orb", "phash", "dhash", "ahash", "histogram"]`
  - `CredentialType = Literal["qr", "barcode", "ocr", "composite"]`
  - `VisualEvidence`: `credential_type`, `credential_value`, `algorithm`, `feature_data` (Base64), `keypoints_count`, `width`, `height`, `extra_features`。
  - `VerifyRequest`: `evidence: VisualEvidence`, `min_score: Optional[float] = 0.60`。
  - `MatchItem`: `id`, `title`, `score`, `secret_text`, `created_at`。
  - `VerifyResponse`: `matched: bool`, `count: int`, `results: List[MatchItem]`, `message: str`。
  - `SecretCreateRequest`: `title: Optional[str]`, `secret_text: str`, `evidence: VisualEvidence`。

---

### 步骤 2：重构数据库模型与数据访问层 (`app/domain/models/`, `app/services/database.py`)

- **文件**：`app/domain/models/secret_entry.py`
  - 改造 `SecretEntry(Model)`：
    - `id = fields.IntField(pk=True)`
    - `title = fields.CharField(max_length=255, null=True)`
    - `credential_type = fields.CharField(max_length=64, default="qr")`
    - `credential_value = fields.CharField(max_length=255, index=True)`（**关键点：取消 unique，建立普通 B-Tree 索引以支持一对多**）
    - `algorithm = fields.CharField(max_length=64, default="orb")`
    - `feature_data = fields.TextField()`（存储 Base64 或 `BinaryField` 二进制特征数据）
    - `keypoints_count = fields.IntField(null=True)`
    - `secret_text = fields.TextField()`
    - `extra_features = fields.JSONField(null=True)`
    - `created_at = fields.DatetimeField(auto_now_add=True)`
    - `viewed_at = fields.DatetimeField(null=True)`
- **文件**：`app/services/database.py`
  - `init_db()`: 配置 Tortoise ORM 加载 `app.domain.models.secret_entry`。
  - `find_candidates_by_credential(credential_value: str) -> List[SecretEntry]`:
    - 执行 `SecretEntry.filter(credential_value=credential_value).all()` 获取全部候选条目。
  - `create_secret_entry(title, secret_text, evidence: VisualEvidence) -> SecretEntry`:
    - 录入新数据并持久化。
  - `update_viewed_at(entry_ids: List[int])`:
    - 批量更新被查看记录的时间戳。

---

### 步骤 3：实现 ORB 特征反序列化与匹配器 (`app/services/matchers/`)

- **文件**：`app/services/matchers/base.py`
  - 定义抽象类 `BaseMatcher(ABC)`，包含抽象方法 `compute_score(feat1: Any, feat2: Any) -> float`。
- **文件**：`app/services/matchers/orb.py`
  - 实现特征反序列化 `decode_orb_descriptors(feature_data: str) -> Optional[np.ndarray]`:
    - 将前端传入的 Base64 字符串解码，还原为 `shape=(N, 32)`, `dtype=np.uint8` 的 NumPy 矩阵。
  - 实现 `ORBMatcher(BaseMatcher)`:
    - 使用 `cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)`。
    - 执行 `knnMatch(query_desc, train_desc, k=2)`。
    - 使用 Lowe's ratio test (`m.distance < 0.75 * n.distance`) 筛选良好匹配点。
    - 评分公式：`score = len(good_matches) / max(len(query_desc), 1)` 并归一化到 `[0.0, 1.0]` 区间。

---

### 步骤 4：构建 Top-5 决策比对引擎 (`app/services/match_engine.py`)

- **文件**：`app/services/match_engine.py`
- **处理流程**：
  1. 接收前端传入的 `VerifyRequest`（包含 `evidence` 与 `min_score`）。
  2. 调用 `find_candidates_by_credential(evidence.credential_value)` 从数据库检索所有候选记录。
  3. 若候选列表为空：直接返回 `matched=False, count=0, results=[], message="未找到与该凭证匹配的记录"`。
  4. 解码前端查询描述子 `query_desc`。
  5. 遍历候选记录：
     - 解码候选条目的 `cand_desc`；
     - 调用 `ORBMatcher.compute_score(query_desc, cand_desc)` 计算 `score`；
     - 若 `score >= min_score`（如 `0.60`），构造 `MatchItem` 并加入匹配结果列表。
  6. 排序与截取：将达标列表按 `score` 降序排列，取前 5 项 `top_results = sorted_items[:5]`。
  7. 决策输出：
     - 若 `top_results` 不为空，更新这批记录的 `viewed_at`，返回 `matched=True, count=len(top_results), results=top_results`；
     - 若为空，返回 `matched=False, count=0, results=[]`。

---

### 步骤 5：路由层重构与统一响应 (`app/routers/` & `app/main.py`)

- **文件**：`app/routers/verify.py`
  - 路由 `POST /api/v1/verify` (入参 `VerifyRequest`，返回 `VerifyResponse`)。
  - 使用 `fastapi.concurrency.run_in_threadpool` 包装 CPU 密集型比对引擎计算。
- **文件**：`app/routers/secrets.py`
  - 路由 `POST /api/v1/secrets` (入参 `SecretCreateRequest`，返回新建的记录详情)。
- **文件**：`app/main.py`
  - 聚合路由至 `/api/v1` 前缀；
  - 保留 `/health` 端点；
  - 注册统一的异常处理器与 CORS 中间件。

---

### 步骤 6：测试验证与基准测试 (`test_apis.py` / `tests/`)

- **单元测试**：
  - Base64 描述子与 NumPy 矩阵互转的正确性测试；
  - ORB KNN 比对与 Lowe's ratio test 评分测试（完全相同图片打分接近 1.0，无关图片接近 0.0）。
- **集成测试**：
  - **一对多场景测试**：使用同一个 `passcode` 录入 3~5 张不同的图片特征及对应密语；
  - 发送其中一张图片的特征 + 该 passcode 进行 verify，断言返回的 Top-1 正确匹配目标密语且 score 最高；
  - 发送不相关图片特征 + 该 passcode，断言返回 `matched=False, results=[]`；
  - 验证多候选集中仅返回高于阈值的前 5 项（Top-5）且排序严格降序。

---

## 4. 交付产物与检查清单 (Checklist)

| 产物项 | 验证标准 |
| :--- | :--- |
| **数据契约** | `app/domain/schemas/evidence.py` 完整定义且对齐 TS 契约 |
| **数据库模型** | `SecretEntry` 去除唯一索引，`credential_value` 索引有效，支持一对多 |
| **算法匹配器** | `ORBMatcher` 正确还原 Base64 并通过 KNN Lowe's ratio 计算打分 |
| **决策引擎** | `MatchEngine` 成功过滤低于阈值条目并按得分降序截取 Top-5 |
| **接口定义** | `POST /api/v1/verify` 与 `POST /api/v1/secrets` 正常工作 |
| **测试套件** | `uv run pytest` 全绿通过，覆盖一对多特征库检索与比对 |
| **代码质量** | `uv run ruff check .` 无警告无报错 |
