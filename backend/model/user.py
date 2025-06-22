from pydantic import BaseModel, Field, validator
from typing import Optional, List
from bson import ObjectId
from enum import Enum

class User(BaseModel):
    username:str
    email_address: str
    password:str

class UserUpdate(BaseModel):
    username:Optional[str]
    email_address:Optional[str]
    password:Optional[str]

class UserResponse(BaseModel):
    id:str= Field(alias="_id")
    username: str
    email_address: str

    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str
        }

class Login(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None
