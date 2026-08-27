from tortoise import fields
from tortoise.models import Model


class SecretEntry(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=255, null=True)
    credential_type = fields.CharField(max_length=64, default="qr")
    credential_value = fields.CharField(
        max_length=255, db_index=True
    )  # 支持 1 对多关联，普通索引非唯一
    algorithm = fields.CharField(max_length=64, default="orb")
    feature_data = fields.TextField()  # 存放 Base64 编码的描述子二进制矩阵数据
    keypoints_count = fields.IntField(null=True)
    secret_text = fields.TextField()
    extra_features = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    viewed_at = fields.DatetimeField(null=True)

    class Meta:
        table = "secret_entries"
