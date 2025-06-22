from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    client: AsyncIOMotorClient = None
    database = None

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "library_db")

async def connect_to_mongo():
    try:
        DatabaseConnection.client = AsyncIOMotorClient(MONGODB_URL)
        DatabaseConnection.database = DatabaseConnection.client[DATABASE_NAME]
        
        # Test the connection
        await DatabaseConnection.client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB at {MONGODB_URL}")
        
        # Create indexes for better performance
        await create_book_indexes()
        await create_user_indexes()
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise e

async def create_book_indexes():
    try:
        books_collection = get_collection("books")
        
        # Create indexes
        await books_collection.create_index("title")
        await books_collection.create_index("author")
        await books_collection.create_index("isbn", unique=True)
        await books_collection.create_index("genre")
        await books_collection.create_index("available")
        await books_collection.create_index([("title", "text"), ("author", "text")])
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Failed to create indexes: {e}")

async def create_user_indexes():
    try:
        user_collection=get_collection("user")
        
        await user_collection.create_index("username", unique=True)
        await user_collection.create_index("email_address", unique=True)
        await user_collection.create_index("password")
        logger.info("user indexes created sucessfully")
    except Exception as e:
        logger.warning(f"failed to create indexes:{e}")
        
def get_database():
    """Get database instance"""
    if DatabaseConnection.database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return DatabaseConnection.database

def get_collection(collection_name: str):
    """Get collection instance"""
    if DatabaseConnection.database is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return DatabaseConnection.database[collection_name]

async def check_database_health():
    """Check if database connection is healthy"""
    try:
        await DatabaseConnection.client.admin.command('ping')
        return True
    except Exception:
        return False