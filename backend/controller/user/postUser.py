from model.user import User
from db.connection import get_collection
from middleware.validator import user_helper
from fastapi import HTTPException
import logging
from middleware.hashing import Hash
from fastapi import HTTPException, Depends, status
from middleware.jwt import create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_user(user:User):
    try:
        collection=get_collection("user")
        hashed_pass = Hash.bcrypt(user.password)
        user_dict= user.model_dump()
        user_dict["password"] = hashed_pass
        new_user= await collection.insert_one(user_dict)
        created_user=await collection.find_one({"_id":new_user.inserted_id})
        
        return user_helper(created_user)
    
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="username already taken")
    except Exception as e:
        logger.error(f"failed to create user:{e}")
        raise HTTPException(status_code=500,detail="failed to create user")
     
async def login(request:OAuth2PasswordRequestForm = Depends()):
    try:
        collection=get_collection("user")
        user = await collection.find_one({"username":request.username})
        access_token = create_access_token(data={"sub": user["username"]})
        user["_id"] = str(user["_id"])
        return {"access_token": access_token, "token_type": "bearer", "user":user}
    except:
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if not Hash.verify(user["password"],request.password):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
