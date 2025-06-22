from fastapi import FastAPI,HTTPException
from model.book import BookResponse, BookUpdate
from db.connection import get_collection
from datetime import datetime
import logging
from bson import ObjectId
import cloudinary
from middleware.validator import book_helper,validate_book_exists
from pymongo.errors import DuplicateKeyError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
COLLECTION_NAME="books"
app=FastAPI()

# Update book
async def update_book(book_id: str, book: BookUpdate):
    try:
        existing_book = await validate_book_exists(book_id)
        collection = get_collection(COLLECTION_NAME)
        
        # Get the raw request data to handle explicit None values
        update_data = {}
        book_dict = book.model_dump()
        
        # Handle all fields that might be updated
        for field, value in book_dict.items():
            if field in book.__fields_set__ or value is not None:
                update_data[field] = value
        
        update_data["updated_at"] = datetime.utcnow()
        
        # Handle image removal logic
        if "image_url" in book.__fields_set__ and not book.image_url:
            # User explicitly wants to remove the image
            update_data["image_url"] = None
            update_data["image_public_id"] = None
            update_data["image_uploaded_at"] = None
            
            # Delete from Cloudinary if public_id exists
            if existing_book.get("image_public_id"):
                try:
                    result = cloudinary.uploader.destroy(existing_book["image_public_id"])
                    logger.info(f"Deleted image from Cloudinary: {existing_book['image_public_id']}, result: {result}")
                except Exception as e:
                    logger.warning(f"Failed to delete image from Cloudinary: {e}")
        
        # Handle new image addition
        elif "image_url" in book.__fields_set__ and book.image_url:
            update_data["image_uploaded_at"] = datetime.utcnow()
            
            # Delete old image if it exists and is different from new one
            if (existing_book.get("image_public_id") and 
                existing_book.get("image_public_id") != book.image_public_id):
                try:
                    result = cloudinary.uploader.destroy(existing_book["image_public_id"])
                    logger.info(f"Deleted old image from Cloudinary: {existing_book['image_public_id']}")
                except Exception as e:
                    logger.warning(f"Failed to delete old image from Cloudinary: {e}")
        
        logger.info(f"Update data being applied: {update_data}")
        
        await collection.update_one(
            {"_id": ObjectId(book_id)}, 
            {"$set": update_data}
        )
        
        updated_book = await collection.find_one({"_id": ObjectId(book_id)})
        return book_helper(updated_book)
    
    except HTTPException:
        raise
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="A book with this ISBN already exists")
    except Exception as e:
        logger.error(f"Failed to update book: {e}")
        raise HTTPException(status_code=500, detail="Failed to update book")

# Update book with image
async def update_book_image(book_id: str, image_url: str, image_public_id: str):
    """Update book with new image information"""
    try:
        existing_book = await validate_book_exists(book_id)
        collection = get_collection(COLLECTION_NAME)
        
        # Delete old image from Cloudinary if exists
        if existing_book.get("image_public_id"):
            try:
                cloudinary.uploader.destroy(existing_book["image_public_id"])
            except Exception as e:
                logger.warning(f"Failed to delete old image: {e}")
        
        # Update with new image information
        update_data = {
            "image_url": image_url,
            "image_public_id": image_public_id,
            "image_uploaded_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await collection.update_one(
            {"_id": ObjectId(book_id)}, 
            {"$set": update_data}
        )
        
        updated_book = await collection.find_one({"_id": ObjectId(book_id)})
        return book_helper(updated_book)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update book image: {e}")
        raise HTTPException(status_code=500, detail="Failed to update book image")