from fastapi import APIRouter, UploadFile, File, Query, Depends
from model.book import BookCreate, BookUpdate, BookResponse, BookSearchResponse, ImageUploadResponse, ImageDeleteRequest
from controller.book.deleteBook import delete_book
from controller.book.getBooks import get_book, get_books
from controller.book.image import upload_image,delete_image,remove_book_image
from controller.book.updateBook import update_book,update_book_image
from controller.book.postBook import create_book
from middleware.oauth import get_current_user

public_router = APIRouter()
protected_router=APIRouter(
    dependencies=[Depends(get_current_user)]
)

# Image upload route
@public_router.post("/upload-image/", response_model=ImageUploadResponse)
async def upload_image_route(file: UploadFile = File(...)):
    return await upload_image(file)

# Image delete route
@protected_router.delete("/delete-image/")
async def delete_image_route(request: ImageDeleteRequest):
    return await delete_image(request)

# Create a new book
@public_router.post("/", response_model=BookResponse)
async def create_book_route(book: BookCreate):
    return await create_book(book)

# Get all books with pagination
@protected_router.get("/", response_model=BookSearchResponse)
async def get_books_route(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page")
):
    return await get_books(page, per_page)

# Get book by ID
@protected_router.get("/{book_id}", response_model=BookResponse)
async def get_book_route(book_id: str):
    return await get_book(book_id)

# Update book details
@protected_router.put("/{book_id}", response_model=BookResponse)
async def update_book_route(book_id: str, book: BookUpdate):
    return await update_book(book_id, book)

# Update book image
@protected_router.put("/{book_id}/image", response_model=BookResponse)
async def update_book_image_route(book_id: str, image_url: str, image_public_id: str):
    return await update_book_image(book_id, image_url, image_public_id)

# Remove book image
@protected_router.delete("/{book_id}/image")
async def remove_book_image_route(book_id: str):
    return await remove_book_image(book_id)

# Delete book
@protected_router.delete("/{book_id}")
async def delete_book_route(book_id: str):
    return await delete_book(book_id)

