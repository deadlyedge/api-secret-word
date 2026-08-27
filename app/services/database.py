from datetime import UTC, datetime

from tortoise import Tortoise
from tortoise.exceptions import ConfigurationError

from app.config import DATABASE_URL
from app.domain.models.secret_entry import SecretEntry
from app.domain.schemas.evidence import VisualEvidence


async def init_db():
    """初始化数据库连接并确保表结构存在"""
    try:
        Tortoise.get_connection("default")
    except ConfigurationError:
        await Tortoise.init(
            db_url=DATABASE_URL,
            modules={"models": ["app.domain.models.secret_entry"]},
        )
    await Tortoise.generate_schemas(safe=True)


async def close_db():
    """关闭数据库连接"""
    try:
        if Tortoise._inited:
            await Tortoise.close_connections()
    except ConfigurationError:
        pass


async def reset_db():
    """重置数据库（删除所有表并重新创建）"""
    await close_db()
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["app.domain.models.secret_entry"]},
    )
    conn = Tortoise.get_connection("default")
    tables = await conn.execute_query_dict(
        "SELECT tablename FROM pg_tables WHERE schemaname='public';"
    )
    for table in tables:
        table_name = table["tablename"]
        await conn.execute_script(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
    await Tortoise.generate_schemas(safe=True)


async def find_candidates_by_credential(credential_value: str) -> list[SecretEntry]:
    """
    根据凭证值 (passcode / credential_value) 查询所有符合条件的候选特征库条目（支持一对多）
    """
    return await SecretEntry.filter(credential_value=credential_value).all()


async def create_secret_entry(
    secret_text: str,
    evidence: VisualEvidence,
    title: str | None = None,
) -> SecretEntry:
    """
    创建并持久化一条新的密语与视觉特征记录
    """
    entry = await SecretEntry.create(
        title=title,
        credential_type=evidence.credential_type,
        credential_value=evidence.credential_value,
        algorithm=evidence.algorithm,
        feature_data=evidence.feature_data,
        keypoints_count=evidence.keypoints_count,
        secret_text=secret_text,
        extra_features=evidence.extra_features,
    )
    return entry


async def update_viewed_at(entry_ids: list[int]):
    """
    批量更新命中的条目的查看时间戳
    """
    if not entry_ids:
        return
    await SecretEntry.filter(id__in=entry_ids).update(viewed_at=datetime.now(UTC))
