from fastapi import FastAPI, HTTPException
from db.connection import get_collection
from bson import ObjectId
import logging
import cloudinary
from middleware.validator import validate_book_exists

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app=FastAPI()
COLLECTION_NAME="books"

async def delete_book(book_id: str):
    try:
        book = await validate_book_exists(book_id)
        collection = get_collection(COLLECTION_NAME)
        
        # Delete from MongoDB
        result = await collection.delete_one({"_id": ObjectId(book_id)})
        
        if result.deleted_count == 1:
            # Clean up image from Cloudinary if exists
            if book.get("image_public_id"):
                try:
                    cloudinary.uploader.destroy(book["image_public_id"])
                except Exception as e:
                    logger.warning(f"Failed to delete image from Cloudinary: {e}")
            
            return {"message": "Book deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Book not found")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete book: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete book")