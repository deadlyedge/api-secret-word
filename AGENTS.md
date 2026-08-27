# AGENTS.md - Backend AI 编码助手指南

本指南为参与后端开发的 AI 助手及工程师制定，明确了项目背景、架构设计、代码规范与开发指令。

---

## 1. 核心架构与设计原则

1. **废弃手动 passcode 输入，以图像凭证为索引**：
   - 系统核心是基于“从图像中读取证据（二维码 `qr`、条形码 `barcode`、OCR 文本 `ocr`、复合凭证 `composite`）”作为身份认证索引 `credential_value`。
   - 禁止引入需要用户在前端输入框输入 `passcode` 的旧版设计。
   - 识别二维码支持强制 HTTPS API 接口模式（如 `https://<host>/api/v1`），调用仅返回纯文本凭证用于后续去中心化校验。
2. **保留 ORB 核心高精度匹配，构建多算法扩展体系**：
   - 保留 OpenCV (`cv2.ORB_create`, `cv2.BFMatcher` / `FLANN`) 作为核心高精度局部特征比对方案，保证尺度与旋转不变性及抗噪识别率。
   - 将 ORB 特征与匹配逻辑解耦封装为标准的 Matcher 策略模式。
   - 提供通用算法扩展接口（`BaseMatcher` / `FeatureExtractor`），支持插拔接入感知哈希（pHash / dHash / aHash）等算法，用于大候选集快速粗筛或多维度辅助打分。
3. **统一命名与数据契约**：
   - 彻底淘汰 `passArea`、`pass_code`、`phrase_code` 等历史混乱字段。
   - 统一使用 `credential_type`、`credential_value`、`algorithm`、`feature_data`、`keypoints_count`、`score`。
4. **分层验证与匹配决策策略**：
   - 第一层（凭证检索层）：基于 `credential_value` 精确索引或过滤候选密语条目。
   - 辅助粗筛层（可选）：当候选集庞大时，使用轻量哈希（pHash/dHash）快速初筛过滤。
   - 第二层（ORB 核心特征精配层）：利用 `cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)` 或基于 Lowe's ratio test 的 KNN 匹配计算 Good Matches 比例与距离评分。
   - 判定标准：凭证匹配一致且 ORB 特征相似度达标（或多层组合校验通过）方可判定验证成功。
5. **分层清晰的后端工程结构**：
   - `api/`: 接口路由、依赖注入、参数校验与标准响应封装。
   - `domain/`: 数据库实体模型 (`models/`) 与 Pydantic 契约 (`schemas/`)。
   - `services/`: 凭证解析（`credential_service.py`）、算法匹配策略（`matchers/`）、综合决策引擎（`match_engine.py`）。
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
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field

AlgorithmType = Literal["orb", "phash", "dhash", "ahash", "histogram"]
CredentialType = Literal["qr", "barcode", "ocr", "composite"]

class VisualEvidence(BaseModel):
    credential_type: CredentialType = Field(..., description="凭证类型")
    credential_value: str = Field(..., description="识别出的凭证值（用于索引）")
    algorithm: AlgorithmType = Field(default="orb", description="核心特征匹配算法")
    feature_data: str = Field(..., description="ORB 描述子序列化数据（Base64/Buffer）或哈希值")
    keypoints_count: Optional[int] = Field(None, description="关键点数量")
    width: int = Field(..., description="图像标准化宽度")
    height: int = Field(..., description="图像标准化高度")
    score: Optional[float] = Field(None, description="置信度或匹配评分")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间戳")
    extra_features: Optional[Dict[str, str]] = Field(None, description="扩展算法特征")

class VerifyRequest(BaseModel):
    evidence: VisualEvidence = Field(..., description="前端识别并提取的视觉证据与特征")

class VerifyResponse(BaseModel):
    matched: bool = Field(..., description="是否匹配成功")
    confidence: float = Field(..., description="综合匹配度得分 0.0 ~ 1.0")
    secret_text: Optional[str] = Field(None, description="匹配成功后解密返回的秘密内容")
    message: str = Field(..., description="结果描述信息")

class SecretCreateRequest(BaseModel):
    title: Optional[str] = Field(None, description="密语标题/备注")
    secret_text: str = Field(..., description="要加密存储的秘密内容")
    evidence: VisualEvidence = Field(..., description="绑定的视觉凭证与特征")
```

---

## 5. 编码实施重点任务清单

1. **统一数据库模型与迁移** (`app/domain/models/secret_entry.py`):
   - 创建 `SecretEntry` 表，字段包含 `id`, `credential_type`, `credential_value`, `algorithm`, `feature_data`, `keypoints_count`, `secret_data`, `extra_features`, `created_at` 等，并对 `credential_value` 建立高效索引。
2. **ORB 描述子序列化与特征匹配器** (`app/services/matchers/orb.py`):
   - 实现前端 Base64 描述子到 NumPy `uint8` 矩阵的还原。
   - 使用 `cv2.BFMatcher` 实现对输入特征与库内特征的快速比对，输出好匹配点比例与置信度。
3. **多算法扩展接口与粗筛** (`app/services/matchers/`):
   - 定义 `BaseMatcher` 抽象基类。
   - 实现可选的哈希匹配器（汉明距离比对），为未来扩展及多维校验提供插件化支持。
4. **决策匹配引擎** (`app/services/match_engine.py`):
   - 步骤一：按 `credential_value` 检索候选记录；
   - 步骤二：若有多条候选且配置了扩展哈希，先用轻量哈希做快速初筛；
   - 步骤三：执行 ORB 精确比对，计算匹配得分；
   - 步骤四：得分超过判定阈值（如 confidence >= 0.75）则返回对应的 `secret_data`。
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
  - OpenCV-Python (`opencv-python` / `cv2`，ORB 特征提取与匹配)
  - Pillow / imagehash (辅助图像哈希扩展)
  - NumPy (数值计算与描述子矩阵处理)
  - pyzbar / pytesseract / easyocr (服务端辅助凭证识别)
- **数据库**: tortoise-orm[asyncpg] (支持 PostgreSQL)
- **代码规范**: Ruff