# API Secret Word

这是一个基于 FastAPI、PostgreSQL 和 OpenCV 的图像特征与凭证（Passcode / Credential）关联检索系统。通过将视觉形象（图像特征）关联到凭证标记（如二维码/条形码/语音等凭证值 passcode），并在服务端建立一对多的特征索引库，实现轻量化的视觉密语验证与检索。

例如：通过一个 passcode 将一副埃菲尔铁塔的照片关联到短句“明天下午三点老地方见”，所有持有这个 passcode 的人通过拍摄特征高度吻合的图片即可解密获取该短句。

---

## 核心业务逻辑与流程

```text
[前端 Camera 采集 / 预处理]
  ├─ 前端自动扫描凭证（QR/条码）或语音/手动输入获取 passcode
  ├─ 图像标准化预处理（分辨率缩放 480p/640p、灰度化、去噪与对比度增强）
  ├─ OpenCV.js (Web Worker) 提取 ORB 描述子特征并转为 Base64
  └─ 组装 VerifyRequest 发送至后端

[后端 API / 匹配决策引擎]
  ├─ 根据 passcode 在数据库中检索所有候选特征库（支持一对多，单个 passcode 可对应多条密语）
  ├─ 使用 OpenCV-Python (BFMatcher + KNN Lowe's ratio test) 逐一计算匹配度评分 (0.0 ~ 1.0)
  ├─ 过滤低于阈值 (如 min_score = 0.60) 的结果，并按匹配得分降序排列
  └─ 返回匹配度高于阈值的前 5 个结果 (Top-5 Match List) 及关联解密文本
```

---

## 核心接口概览

- **POST `/api/v1/verify`**: 接收前端预处理提取好的 `VisualEvidence`（包含 `passcode` / `credential_value` 与 Base64 描述子），在数据库中查找该 passcode 下的所有特征库并比对，返回不匹配或匹配度高于阈值的前五结果（Top-5）。
- **POST `/api/v1/secrets`**: 录入新密语，绑定对应的 `credential_value`（passcode）与图像特征描述子。
- **GET `/health`**: 健康检查接口。

---

## 技术栈

- **语言环境**: Python 3.12+ (使用 `uv` 管理依赖与环境)
- **Web 框架**: FastAPI + Uvicorn
- **ORM & 数据库**: Tortoise-ORM (PostgreSQL)
- **图像算法与计算**: OpenCV (`opencv-python-headless`), NumPy, Pillow / imagehash
- **数据验证**: Pydantic v2
- **代码规范**: Ruff

---

## 环境配置与运行

### 1. 依赖同步 (uv)

本项目严格使用 `uv`：

```bash
# 同步依赖
uv sync
```

### 2. 配置环境变量

创建或编辑 `.env` 文件：

```env
DATABASE_URL=postgres://user:password@host:port/dbname
```

### 3. 运行服务

```bash
# 启动 FastAPI 开发服务器
uv run uvicorn app.main:app --reload --port 8000
```

### 4. 测试与代码检查

```bash
# 运行单元与集成测试
uv run pytest

# 代码检查与格式化
uv run ruff check .
uv run ruff format .
```

---

## 项目代码结构

```
api-secret-word/
├── AGENTS.md                  # 后端 AI 编码助手指导规范
├── README.md                  # 项目概述与运行说明
├── documents/                 # 架构与重构实施文档
│   ├── 重构实施方案 v3.md       # 架构重构详细方案 (v3.1)
│   └── 重构工作计划.md          # 分阶段实施工作清单
├── app/
│   ├── config.py              # 全局配置与环境变量
│   ├── main.py                # FastAPI 入口与中间件
│   ├── domain/                # 领域模型与数据契约
│   │   ├── models/            # Tortoise ORM 实体模型
│   │   └── schemas/           # Pydantic v2 请求/响应契约
│   ├── routers/               # API 路由层 (v1)
│   ├── services/              # 业务服务层
│   │   ├── database.py        # 数据库操作封装
│   │   ├── match_engine.py    # 多候选 Top-5 匹配决策引擎
│   │   └── matchers/          # ORB 及多算法策略实现
│   └── utils/                 # 通用工具库
├── test_data/                 # 测试图片与特征数据集
└── pyproject.toml             # uv / Python 项目元数据
```

---

## 开发与重构参考

- 详细架构与契约设计：请参阅 [`documents/重构实施方案 v3.md`](documents/重构实施方案%20v3.md)
- 具体开发排期与阶段任务：请参阅 [`documents/重构工作计划.md`](documents/重构工作计划.md)
- AI 协作与编码规范：请参阅 [`AGENTS.md`](AGENTS.md)
