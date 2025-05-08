from dotenv import load_dotenv
from os import getenv

load_dotenv()  # Load environment variables from .env file


# Constants with validation
# ORB feature points to detect, min_value=100, max_value=2000
SAMPLE_POINTS = int(getenv("IMAGE_SAMPLE_POINTS", 500))

# Threshold for good match ratio, 0.5 to 0.75 is a good range
MATCH_POINT = float(getenv("IMAGE_MATCH_POINT", 0.7))

# Database configuration
DATABASE_URL = getenv(
    "DATABASE_URL", "postgres://user:password@localhost:5432/dbname"
).replace("postgresql://", "postgres://")

# Other configurations can be added here
