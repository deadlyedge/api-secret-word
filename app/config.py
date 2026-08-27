from os import getenv

from dotenv import load_dotenv

load_dotenv()

# Constants with validation
# ORB feature points to detect, min_value=100, max_value=2000
SAMPLE_POINTS = int(getenv("IMAGE_SAMPLE_POINTS", "500"))

# Threshold for good match ratio, 0.5 to 0.75 is a good range
MATCH_POINT = float(getenv("IMAGE_MATCH_POINT", "0.60"))

# Database configuration
raw_db_url = getenv("DATABASE_URL", "sqlite://:memory:")
# Tortoise-ORM 期望 postgres:// 协议 scheme（若配置为 postgresql:// 则自动转换）
if raw_db_url.startswith("postgresql://"):
    DATABASE_URL = raw_db_url.replace("postgresql://", "postgres://", 1)
else:
    DATABASE_URL = raw_db_url
