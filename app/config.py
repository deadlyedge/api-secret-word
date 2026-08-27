from os import getenv

from dotenv import load_dotenv

load_dotenv()

# Constants with validation
# ORB feature points to detect, min_value=100, max_value=2000
SAMPLE_POINTS = int(getenv("IMAGE_SAMPLE_POINTS", "500"))

# Threshold for good match ratio, 0.5 to 0.75 is a good range
MATCH_POINT = float(getenv("IMAGE_MATCH_POINT", "0.60"))

# Database configuration
DATABASE_URL = getenv("DATABASE_URL", "sqlite://:memory:")
