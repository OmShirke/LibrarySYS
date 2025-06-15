from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    isbn: str = Field(..., min_length=1, max_length=17)
    publication_year: int = Field(..., ge=1000, le=2025)
    genre: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    available: bool = True
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None  # Cloudinary public ID for management
    
    @validator('isbn')
    def validate_isbn(cls, v):
        # Remove any hyphens or spaces
        isbn = v.replace('-', '').replace(' ', '')
        return isbn

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    isbn: Optional[str] = Field(None, min_length=1, max_length=17)
    publication_year: Optional[int] = Field(None, ge=1000, le=2025)
    genre: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=2000)
    available: Optional[bool] = None
    image_url: Optional[str] = None
    image_public_id: Optional[str] = None
    
    @validator('isbn')
    def validate_isbn(cls, v):
        if v is None:
            return v
        # Remove any hyphens or spaces
        isbn = v.replace('-', '').replace(' ', '')
        return isbn

class BookResponse(BookBase):
    id: str = Field(alias="_id")
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    image_uploaded_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: str
        }

class BookSearchResponse(BaseModel):
    books: List[BookResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class ImageUploadResponse(BaseModel):
    image_url: str
    image_public_id: str
    message: str
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None
    bytes: Optional[int] = None

class ImageDeleteRequest(BaseModel):
    public_id: str

class DatabaseHealthResponse(BaseModel):
    status: str
    database: str
    collections: List[str]
    timestamp: datetime