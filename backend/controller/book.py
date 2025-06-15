from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import cloudinary
import cloudinary.uploader
import os
from db.connection import get_db, BookDB
from model.book import Book, BookCreate, BookUpdate

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

router = APIRouter()

# Get all books
@router.get("/books", response_model=List[Book])
def get_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    books = db.query(BookDB).offset(skip).limit(limit).all()
    return books

# Get a specific book
@router.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# Create a new book with optional image upload (single endpoint)
@router.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(
    title: str = Form(...),
    author: str = Form(...),
    isbn: str = Form(...),
    publication_year: int = Form(...),
    genre: str = Form(...),
    available: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Check if book with this ISBN already exists
    existing_book = db.query(BookDB).filter(BookDB.isbn == isbn).first()
    if existing_book:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    image_id = None
    image_url = None
    
    # Upload image to Cloudinary if provided
    if image:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        try:
            sanitized_isbn = isbn.replace('-', '').replace(' ', '')
            custom_public_id = f"book_covers/{sanitized_isbn}"
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                image.file,
                public_id=custom_public_id,
                folder="library_books",
                resource_type="image",
                overwrite=True,
                transformation=[
                    {'width': 400, 'height': 600, 'crop': 'fill'},
                    {'quality': 'auto:good'}
                ]
            )
            
            image_id = upload_result.get('public_id')
            image_url = upload_result.get('secure_url')
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
    
    # Create book record
    book_data = {
        "title": title,
        "author": author,
        "isbn": isbn,
        "publication_year": publication_year,
        "genre": genre,
        "available": available,
        "image_id": image_id,
        "image_url": image_url
    }
    
    db_book = BookDB(**book_data)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

# Update a book
@router.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book_update: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    update_data = book_update.model_dump(exclude_unset=True)
    
    # Check ISBN uniqueness if updating ISBN
    if "isbn" in update_data:
        existing_book = db.query(BookDB).filter(
            BookDB.isbn == update_data["isbn"], 
            BookDB.id != book_id
        ).first()
        if existing_book:
            raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    for field, value in update_data.items():
        setattr(book, field, value)
    
    db.commit()
    db.refresh(book)
    return book

# Update book with new image
@router.put("/books/{book_id}/upload", response_model=Book)
async def update_book_with_image(
    book_id: int,
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    publication_year: Optional[int] = Form(None),
    genre: Optional[str] = Form(None),
    available: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check ISBN uniqueness if updating ISBN
    if isbn and isbn != book.isbn:
        existing_book = db.query(BookDB).filter(
            BookDB.isbn == isbn, 
            BookDB.id != book_id
        ).first()
        if existing_book:
            raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    # Handle image upload if provided
    if image:
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        try:
            # Delete old image if exists
            if book.image_id:
                try:
                    cloudinary.uploader.destroy(book.image_id)
                except:
                    pass  # Continue if deletion fails
            
            # Use new ISBN if provided, otherwise use existing
            current_isbn = isbn if isbn else book.isbn
            sanitized_isbn = current_isbn.replace('-', '').replace(' ', '')
            custom_public_id = f"book_covers/{sanitized_isbn}"
            
            # Upload new image
            upload_result = cloudinary.uploader.upload(
                image.file,
                public_id=custom_public_id,
                folder="library_books",
                resource_type="image",
                overwrite=True,
                transformation=[
                    {'width': 400, 'height': 600, 'crop': 'fill'},
                    {'quality': 'auto:good'}
                ]
            )
            
            book.image_id = upload_result.get('public_id')
            book.image_url = upload_result.get('secure_url')
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
    
    # Update other fields
    update_fields = {
        "title": title,
        "author": author,
        "isbn": isbn,
        "publication_year": publication_year,
        "genre": genre,
        "available": available
    }
    
    for field, value in update_fields.items():
        if value is not None:
            setattr(book, field, value)
    
    db.commit()
    db.refresh(book)
    return book

# Delete a book
@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Delete image from Cloudinary if exists
    if book.image_id:
        try:
            cloudinary.uploader.destroy(book.image_id)
        except Exception as e:
            print(f"Failed to delete image from Cloudinary: {str(e)}")
            # Continue with book deletion even if image deletion fails
    
    db.delete(book)
    db.commit()
    return

# Search books by title or author
@router.get("/books/search/{query}", response_model=List[Book])
def search_books(query: str, db: Session = Depends(get_db)):
    books = db.query(BookDB).filter(
        (BookDB.title.contains(query)) | (BookDB.author.contains(query))
    ).all()
    return books

# Get available books only
@router.get("/books/available/list", response_model=List[Book])
def get_available_books(db: Session = Depends(get_db)):
    books = db.query(BookDB).filter(BookDB.available == True).all()
    return books