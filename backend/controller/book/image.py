from fastapi import FastAPI, UploadFile, HTTPException, File
from model.book import( ImageUploadResponse, ImageDeleteRequest)
import cloudinary
import cloudinary.uploader
import logging
from bson import ObjectId
from db.connection import get_collection
from datetime import datetime
from middleware.validator import validate_book_exists

COLLECTION_NAME="books"

app=FastAPI()

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]
MAX_FILE_SIZE = 5 * 1024 * 1024  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Image upload endpoint
async def upload_image(file: UploadFile = File(...)):
    try:
        # Validate file type
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not supported. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
            )
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end of file
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"File size must be less than {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file.file,
            folder="library_books",
            resource_type="image",
            transformation=[
                {"width": 400, "height": 600, "crop": "fill"},
                {"quality": "auto"},
                {"format": "auto"}
            ]
        )
        
        return ImageUploadResponse(
            image_url=result["secure_url"],
            image_public_id=result["public_id"],
            message="Image uploaded successfully",
            width=result.get("width"),
            height=result.get("height"),
            format=result.get("format"),
            bytes=result.get("bytes")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

# Delete image endpoint
async def delete_image(request: ImageDeleteRequest):
    try:
        result = cloudinary.uploader.destroy(request.public_id)
        return {"message": "Image deleted successfully", "result": result}
    except Exception as e:
        logger.error(f"Image deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image deletion failed: {str(e)}")
    
async def remove_book_image(book_id: str):
    try:
        existing_book = await validate_book_exists(book_id)
        collection = get_collection(COLLECTION_NAME)
        
        if existing_book.get("image_public_id"):
            try:
                cloudinary.uploader.destroy(existing_book["image_public_id"])
            except Exception as e:
                logger.warning(f"Failed to delete image from Cloudinary: {e}")
        
        # Remove image fields from book
        await collection.update_one(
            {"_id": ObjectId(book_id)}, 
            {"$unset": {
                "image_url": "",
                "image_public_id": "",
                "image_uploaded_at": ""
            },
            "$set": {
                "updated_at": datetime.utcnow()
            }}
        )
        
        return {"message": "Image removed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove book image: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove book image")