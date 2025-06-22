from fastapi import FastAPI, HTTPException, Query
from model.book import BookSearchResponse
from db.connection import get_collection
import logging
from middleware.validator import book_helper
from typing import Optional
from middleware.validator import validate_book_exists

COLLECTION_NAME="books"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
async def get_book(book_id: str):
    book = await validate_book_exists(book_id)
    return book_helper(book)

# Search books
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