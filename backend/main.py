from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cloudinary
import os
from dotenv import load_dotenv
import logging
from pymongo.errors import DuplicateKeyError
from routes.bookRoutes import public_router as book_public_router
from routes.bookRoutes import protected_router as book_protected_router
from routes.userRoutes import public_router as user_public_router
from routes.userRoutes import protected_router as user_protected_router
# from model.user import User
# from middleware.oauth import get_current_user

from db.connection import (
    connect_to_mongo,
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

app.include_router(book_public_router, prefix="/books", tags=["Books"])
app.include_router(user_public_router, prefix="/user", tags=["Users"])
app.include_router(book_protected_router, prefix="/books", tags=["Books"])
app.include_router(user_protected_router, prefix="/user", tags=["Users"])


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

# def read_root(current_user:User = Depends(get_current_user)):
# 	return {"data":"Hello OWrld"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)