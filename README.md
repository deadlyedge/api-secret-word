# API Secret Word

这是一个基于 FastAPI 和 PostgreSQL 的图片+暗语信息检索 API。通过上传图片的 ORB 特征和暗语（pass code），实现信息的存储与安全检索。

## 功能简介

- **/maker**: 接收图片（URL）、暗语和文字信息，提取图片特征并存入数据库。暗语唯一，重复会返回错误。
- **/passCheck**: 检查暗语是否已被使用。
- **/vTag**: 通过暗语和图片进行匹配，若图片特征相似则返回对应文字信息。
- **/health**: 健康检查接口。

## 技术栈

- Python 3.9+
- FastAPI
- Tortoise ORM（PostgreSQL）
- OpenCV (ORB 特征提取)
- NumPy
- Uvicorn

## 环境配置

1. 安装依赖：

```bash
uv sync
```

2. 配置 `.env` 文件，设置数据库连接字符串：

```
DATABASEURL=postgres://user:password@host:port/dbname
```

## 运行

1. 初始化数据库（示例）：

```python
import asyncio
from app.database import init_db

asyncio.run(init_db())
```

2. 启动服务：

```bash
uvicorn app.main:app --reload
```

3. 访问接口：

- POST `/maker`
- POST `/passCheck`
- POST `/vTag`
- GET `/health`

## 代码结构

```
app/
├── config.py          # 配置与常量
├── database.py        # 数据库模型与连接
├── main.py            # FastAPI 应用入口
├── routers/           # 路由模块
│   ├── maker.py
│   ├── pass_check.py
│   └── vtag.py
└── services/          # 业务逻辑服务
    ├── db_service.py
    └── image_service.py
```

## 注意事项

- 图片通过 URL 上传，服务端会下载并提取 ORB 特征。
- 暗语（pass code）必须唯一。
- 数据库使用 PostgreSQL，连接字符串需正确配置。
- 需确保安装并配置好 PostgreSQL 服务。

## 未来扩展

- 支持基于模糊描述和暗语的文本检索。
- 增加认证和安全机制。
- 优化图像特征匹配算法。
- 根据现有的api结构，在 @/test_data/ 中生成一些测试数据，并写一个测试程序调用这些测试数据来测试我的app

---

欢迎反馈和贡献！
