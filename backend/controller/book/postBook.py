from fastapi import FastAPI,HTTPException
import logging
from db.connection import get_collection
from datetime import datetime
from model.book import BookResponse,BookCreate
from middleware.validator import book_helper
from pymongo.errors import DuplicateKeyError

COLLECTION_NAME="books"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create book
async def create_book(book: BookCreate):
    try:
        collection = get_collection(COLLECTION_NAME)
        
        book_dict = book.model_dump()
        book_dict["created_at"] = datetime.utcnow()
        book_dict["updated_at"] = datetime.utcnow()
        
        if book_dict.get("image_url"):
            book_dict["image_uploaded_at"] = datetime.utcnow()
        
        new_book = await collection.insert_one(book_dict)
        created_book = await collection.find_one({"_id": new_book.inserted_id})
        return book_helper(created_book)
    
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="A book with this ISBN already exists")
    except Exception as e:
        logger.error(f"Failed to create book: {e}")
        raise HTTPException(status_code=500, detail="Failed to create book")