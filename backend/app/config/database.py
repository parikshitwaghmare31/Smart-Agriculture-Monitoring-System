"""
MongoDB connection handling using Motor (async driver).
Exposes a single shared client/database instance for the app lifecycle.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
from app.config.logging_config import app_logger


class Database:
    client: AsyncIOMotorClient = None
    db = None


database = Database()


async def connect_to_mongo():
    try:
        database.client = AsyncIOMotorClient(
            settings.MONGO_URI, serverSelectionTimeoutMS=5000, tz_aware=True
        )
        database.db = database.client[settings.MONGO_DB_NAME]
        # Force a round-trip to verify connectivity early
        await database.client.admin.command("ping")
        app_logger.info(f"Connected to MongoDB at {settings.MONGO_URI} (db={settings.MONGO_DB_NAME})")

        # Helpful indexes for query performance
        await database.db[settings.SENSOR_COLLECTION].create_index("timestamp")
        await database.db[settings.PREDICTION_COLLECTION].create_index("timestamp")
    except Exception as e:
        app_logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    if database.client:
        database.client.close()
        app_logger.info("MongoDB connection closed")


def get_database():
    return database.db
