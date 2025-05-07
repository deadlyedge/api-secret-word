import asyncio
from app.services.database import reset_db

if __name__ == "__main__":
    asyncio.run(reset_db())
    print("Database has been reset.")
