from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from db.connection import get_db, BookDB
from model.book import Book, BookCreate, BookUpdate

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

# Create a new book
@router.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    existing_book = db.query(BookDB).filter(BookDB.isbn == book.isbn).first()
    if existing_book:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    db_book = BookDB(**book.model_dump())
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

# Delete a book
@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
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