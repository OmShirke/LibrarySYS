from fastapi import FastAPI, HTTPException, File, UploadFile, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import List, Optional
import cloudinary
import cloudinary.uploader
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from pymongo.errors import DuplicateKeyError

from db.connection import (
    connect_to_mongo,
    get_collection
)
from model.book import (
    BookCreate, BookUpdate, BookResponse, BookSearchResponse,
    ImageUploadResponse, ImageDeleteRequest
)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

COLLECTION_NAME = "books"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp", "image/gif"]

app = FastAPI(
    title="Library Management System",
    description="A comprehensive library management system with image upload support",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",
    "https://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    try:
        await connect_to_mongo()
        logger.info("Application startup completed")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise e

# Exception handlers
@app.exception_handler(DuplicateKeyError)
async def duplicate_key_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"detail": "A book with this ISBN already exists"}
    )

# Helper function to convert ObjectId to string
def book_helper(book) -> dict:
    return {
        "id": str(book["_id"]),
        "title": book["title"],
        "author": book["author"],
        "isbn": book["isbn"],
        "publication_year": book["publication_year"],
        "genre": book["genre"],
        "description": book.get("description"),
        "available": book["available"],
        "image_url": book.get("image_url"),
        "image_public_id": book.get("image_public_id"),
        "image_uploaded_at": book.get("image_uploaded_at"),
        "created_at": book.get("created_at"),
        "updated_at": book.get("updated_at")
    }

# Validation helpers
def validate_object_id(obj_id: str) -> ObjectId:
    if not ObjectId.is_valid(obj_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return ObjectId(obj_id)

async def validate_book_exists(book_id: str) -> dict:
    collection = get_collection(COLLECTION_NAME)
    book = await collection.find_one({"_id": validate_object_id(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# Image upload endpoint
@app.post("/upload-image/", response_model=ImageUploadResponse)
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
@app.delete("/delete-image/")
async def delete_image(request: ImageDeleteRequest):
    try:
        result = cloudinary.uploader.destroy(request.public_id)
        return {"message": "Image deleted successfully", "result": result}
    except Exception as e:
        logger.error(f"Image deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image deletion failed: {str(e)}")

# Create book
@app.post("/books/", response_model=BookResponse)
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

# Get all books with pagination
@app.get("/books/", response_model=BookSearchResponse)
async def get_books(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
):
    try:
        collection = get_collection(COLLECTION_NAME)
        
        skip = (page - 1) * per_page
        
        # Get total count
        total = await collection.count_documents({})
        
        # Get books for current page
        books = await collection.find().skip(skip).limit(per_page).to_list(per_page)
        
        return BookSearchResponse(
            books=[book_helper(book) for book in books],
            total=total,
            page=page,
            per_page=per_page,
            has_next=skip + per_page < total,
            has_prev=page > 1
        )
    
    except Exception as e:
        logger.error(f"Failed to get books: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve books")

# Get book by ID
@app.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str):
    book = await validate_book_exists(book_id)
    return book_helper(book)

# Update book
@app.put("/books/{book_id}", response_model=BookResponse)
async def update_book(book_id: str, book: BookUpdate):
    try:
        existing_book = await validate_book_exists(book_id)
        collection = get_collection(COLLECTION_NAME)
        
        # Get the raw request data to handle explicit None values
        update_data = {}
        book_dict = book.dict()
        
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
@app.put("/books/{book_id}/image", response_model=BookResponse)
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

# Remove book image
@app.delete("/books/{book_id}/image")
async def remove_book_image(book_id: str):
    try:
        existing_book = await validate_book_exists(book_id)
        collection = get_collection(COLLECTION_NAME)
        
        # Delete image from Cloudinary if exists
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

# Delete book
@app.delete("/books/{book_id}")
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

# Search books
@app.get("/books/search/", response_model=BookSearchResponse)
async def search_books(
    title: Optional[str] = Query(None, description="Search by title"),
    author: Optional[str] = Query(None, description="Search by author"),
    genre: Optional[str] = Query(None, description="Search by genre"),
    available: Optional[bool] = Query(None, description="Filter by availability"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
):
    try:
        collection = get_collection(COLLECTION_NAME)
        query = {}
        
        if title:
            query["title"] = {"$regex": title, "$options": "i"}
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
        if genre:
            query["genre"] = {"$regex": genre, "$options": "i"}
        if available is not None:
            query["available"] = available
        
        skip = (page - 1) * per_page
        
        # Get total count
        total = await collection.count_documents(query)
        
        # Get books for current page
        books = await collection.find(query).skip(skip).limit(per_page).to_list(per_page)
        
        return BookSearchResponse(
            books=[book_helper(book) for book in books],
            total=total,
            page=page,
            per_page=per_page,
            has_next=skip + per_page < total,
            has_prev=page > 1
        )
    
    except Exception as e:
        logger.error(f"Failed to search books: {e}")
        raise HTTPException(status_code=500, detail="Failed to search books")

# Health check
@app.get("/")
async def root():
    return {
        "message": "Library Management System API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "books": "/books/",
            "search": "/books/search/",
            "upload_image": "/upload-image/",
            "health": "/health/database",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)