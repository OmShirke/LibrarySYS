from fastapi import HTTPException
from bson import ObjectId
from db.connection import get_collection


# Validation helpers
def validate_object_id(obj_id: str) -> ObjectId:
    if not ObjectId.is_valid(obj_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return ObjectId(obj_id)

async def validate_book_exists(book_id: str) -> dict:
    COLLECTION_NAME="books" 
    collection = get_collection(COLLECTION_NAME)
    book = await collection.find_one({"_id": validate_object_id(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

async def validate_user_exists(user_id: str) -> dict:
    COLLECTION_NAME="user" 
    collection = get_collection(COLLECTION_NAME)
    user = await collection.find_one({"_id": validate_object_id(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="Book not found")
    return user

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

def user_helper(user)->dict:
    return{
        "id":str(user["_id"]),
        "username":user["username"],
        "password":user["password"],
        "email_address":user["email_address"]
    }
