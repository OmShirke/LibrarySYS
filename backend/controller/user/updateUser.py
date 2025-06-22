from model.user import User
from middleware.validator import validate_user_exists
from db.connection import get_collection
import logging
from bson import ObjectId
from middleware.validator import user_helper
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_user(user_id: str, user:User):
    try:
        existing_user=await validate_user_exists(user_id)
        collection=get_collection("user")

        update_data={}
        user_dict=user.model_dump()

        for field, value in user_dict.items():
            if field in user.model__fields_set__ or value is not None:
                update_data[field] = value

        logger.info("update data being applied: {update_data}")

        await collection.update_one(
            {"-id":ObjectId(user_id)},
            {"$set":update_data}
        )

        updated_user=await collection.find_one({"_id": ObjectId(user_id)})
        return user_helper(update_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")