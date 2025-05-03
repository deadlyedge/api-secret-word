from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# Constants
SAMPLE_POINTS = int(
    os.getenv("IMAGE_SAMPLE_POINTS", 500)
)  # ORB feature points to detect
MATCH_POINT = float(
    os.getenv("IMAGE_MATCH_POINT", 0.75)
)  # Threshold for good match ratio

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgres://user:password@localhost:5432/dbname"
)

# Other configurations can be added here
