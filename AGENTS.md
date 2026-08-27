# AGENTS.md - Backend AI 编码助手指南

本指南为参与后端开发的 AI 助手及工程师制定，明确了项目背景、架构设计、代码规范与开发指令。

---

## 1. 核心架构与设计原则

1. **凭证索引与一对多特征库检索**：
   - 系统的核心价值在于将一个视觉形象（图像特征）关联到一个凭证标记（`passcode` / `credential_value`），并在服务端建立一对多的特征索引库，实现去中心化或轻量化的视觉密语验证与检索。
   - 前端优先通过相机画面自动识别凭证（二维码 `qr`、条形码 `barcode`）或语音识别提取 `passcode`，手动输入框作为备选项。
   - 后端根据前端发来的 `passcode`（`credential_value`），在数据库中检索出**所有符合该 passcode 的候选特征库条目（支持一对多，单个 passcode 可对应多个已存密语/特征）**。
2. **保留 ORB 核心高精度匹配，构建多算法扩展体系**：
   - 保留 OpenCV (`cv2.ORB_create`, `cv2.BFMatcher` / `FLANN`) 作为核心高精度局部特征比对方案，保证尺度与旋转不变性及抗噪识别率。
   - 将 ORB 特征与匹配逻辑解耦封装为标准的 Matcher 策略模式。
   - 提取各候选条目的特征描述子与前端提交特征逐一精配，计算相似度评分（`score`，0.0~1.0）。
   - 提供通用算法扩展接口（`BaseMatcher` / `FeatureExtractor`），支持插拔接入感知哈希（pHash / dHash / aHash）等算法，用于大候选集快速粗筛或多维度辅助打分。
3. **决策引擎与 Top-5 结果过滤返回**：
   - 比对完成后，按阈值过滤（如 `score >= min_score` / `0.60`）；
   - 将符合阈值的候选结果按 `score` 降序排列，**截取并返回高于阈值的前 5 个结果（Top-5）**以及对应关联的密语内容；
   - 若无可达标项，返回不匹配响应。
4. **统一命名与数据契约**：
   - 彻底淘汰 `passArea`、`pass_code`、`phrase_code` 等历史混乱字段。
   - 统一使用 `credential_type`、`credential_value`、`algorithm`、`feature_data`、`keypoints_count`、`score`。
5. **分层清晰的后端工程结构**：
   - `api/` 或 `routers/`: 接口路由、依赖注入、参数校验与标准响应封装。
   - `domain/`: 数据库实体模型 (`models/`) 与 Pydantic 契约 (`schemas/`)。
   - `services/`: 数据库服务（`database.py`）、算法匹配策略（`matchers/`）、综合决策引擎（`match_engine.py`）。
   - `infra/`: 数据库连接、安全控制与审计日志。

---

## 2. 常用开发与环境命令 (uv)

本项目**严格使用 `uv`** 管理 Python 虚拟环境与依赖：

```bash
# 1. 虚拟环境管理
uv venv                       # 创建 .venv
.venv\Scripts\Activate.ps1   # 激活虚拟环境 (Windows)

# 2. 依赖管理
uv add <package_name>         # 添加生产依赖 (自动写入 pyproject.toml)
uv add --dev <package_name>   # 添加开发依赖
uv remove <package_name>      # 移除依赖
uv sync                       # 依照 lockfile 同步依赖

# 3. 运行与测试
uv run uvicorn app.main:app --reload --port 8000 # 启动开发服务器
uv run pytest                                    # 运行单元与集成测试
uv run ruff check .                              # 代码 Lint 检查
uv run ruff format .                             # 代码格式化
uv run mypy app                                  # 类型检查
```

---

## 3. 代码风格与规范

- **Python 版本**: Python 3.12+
- **类型注解**: 全面采用严格类型注解（使用 `typing` 和 Pydantic v2 `BaseModel`）。
- **异步原则**: FastAPI 路由函数若涉及 I/O 操作尽量采用 `async def`；CPU 密集的图像重计算与 ORB 矩阵比对须使用 `run_in_threadpool` 处理，避免阻塞主事件循环。
- **错误处理**: 统一抛出 `HTTPException` 或自定义领域异常，并在全局异常处理器中转换为统一的 JSON 格式：
  ```json
  {
    "success": false,
    "code": "CREDENTIAL_MISMATCH",
    "message": "未能匹配有效的图像凭证",
    "data": null
  }
  ```

---

## 4. 关键数据结构与核心 Schema

在 `app/domain/schemas/evidence.py` 中必须保证以下契约的前后端对齐：

```python
from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

AlgorithmType = Literal["orb", "phash", "dhash", "ahash", "histogram"]
CredentialType = Literal["qr", "barcode", "ocr", "composite"]

class VisualEvidence(BaseModel):
    credential_type: CredentialType = Field(..., description="凭证类型 (qr/barcode)")
    credential_value: str = Field(..., description="识别出的凭证值/passcode")
    algorithm: AlgorithmType = Field(default="orb", description="核心特征提取算法")
    feature_data: str = Field(..., description="Base64 编码的描述子二进制矩阵")
    keypoints_count: Optional[int] = Field(None, description="关键点数量")
    width: int = Field(..., description="标准化宽度")
    height: int = Field(..., description="标准化高度")
    extra_features: Optional[Dict[str, str]] = Field(None, description="可选辅助哈希特征")

class VerifyRequest(BaseModel):
    evidence: VisualEvidence = Field(..., description="前端预处理并提取的凭证与特征")
    min_score: Optional[float] = Field(default=0.60, description="最低有效匹配阈值 (0.0~1.0)")

class MatchItem(BaseModel):
    id: str = Field(..., description="密语记录 ID")
    title: Optional[str] = Field(None, description="密语标题/描述")
    score: float = Field(..., description="匹配相似度得分 (0.0~1.0)")
    secret_text: Optional[str] = Field(None, description="关联的解密内容")
    created_at: datetime = Field(..., description="创建时间")

class VerifyResponse(BaseModel):
    matched: bool = Field(..., description="是否存在达标匹配项")
    count: int = Field(..., description="命中数量 (<= 5)")
    results: List[MatchItem] = Field(default_factory=list, description="匹配度高于阈值的前五结果（按 score 降序）")
    message: str = Field(..., description="结果描述信息")

class SecretCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="密语标题/备注")
    secret_text: str = Field(..., description="密语内容")
    evidence: VisualEvidence = Field(..., description="绑定的凭证与特征")
```

---

## 5. 编码实施重点任务清单

1. **统一数据库模型与迁移** (`app/domain/models/secret_entry.py` / `app/services/database.py`):
   - 创建/改造 `SecretEntry` 表，字段包含 `id`, `credential_type`, `credential_value`, `algorithm`, `feature_data`, `keypoints_count`, `secret_text`, `extra_features`, `created_at` 等。
   - **注意**：`credential_value` 为普通非唯一索引（`index=True`），支持一对多存储。
2. **ORB 描述子序列化与特征匹配器** (`app/services/matchers/orb.py`):
   - 实现前端 Base64 描述子到 NumPy `uint8` 矩阵的还原 `(N, 32)`。
   - 使用 `cv2.BFMatcher(cv2.NORM_HAMMING)` 执行 KNN (`k=2`) 匹配与 Lowe's ratio test (ratio <= 0.75) 计算 Good Matches 匹配度得分。
3. **多算法扩展接口与粗筛** (`app/services/matchers/`):
   - 定义 `BaseMatcher` 抽象基类。
   - 实现可选的哈希匹配器（汉明距离比对），为未来扩展及多维校验提供插件化支持。
4. **决策匹配引擎** (`app/services/match_engine.py`):
   - 步骤一：按 `credential_value` (passcode) 检索数据库中全部候选记录（可能存在多条）；
   - 步骤二：逐一比对候选特征与前端提交的特征，计算匹配得分；
   - 步骤三：过滤 `score >= min_score`（如 0.60），并按得分从高到低降序排序；
   - 步骤四：截取 Top-5 匹配项，组装 `VerifyResponse` 并返回。
5. **安全控制与传输规范**:
   - 配置严格的 CORS 白名单；
   - 接口调用限流防刷（Rate Limiting）；
   - 数据最小化原则：避免持久化存储用户完整高分辨率原图，仅保存特征描述子摘要。

---

## 6. 技术栈与工具参考

- **包与环境管理**: `uv` (Fast Python package installer and resolver)
- **Web 框架**: FastAPI + Uvicorn
- **数据验证与序列化**: Pydantic v2
- **图像处理与算法库**: 
  - OpenCV-Python (`opencv-python-headless` / `cv2`，ORB 特征提取与匹配)
  - Pillow / imagehash (辅助图像哈希扩展)
  - NumPy (数值计算与描述子矩阵处理)
- **数据库**: tortoise-orm[asyncpg] (支持 PostgreSQL)
- **代码规范**: Ruff
