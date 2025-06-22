from model.user import UserResponse, User, UserUpdate, Login, LoginResponse
from controller.user.postUser import create_user, login
from controller.user.updateUser import update_user
from fastapi import APIRouter, Depends
from middleware.oauth import get_current_user

public_router = APIRouter()
protected_router=APIRouter(
    dependencies=[Depends(get_current_user)]
)

@public_router.post("/register", response_model=UserResponse)
async def create_user_route(user: User):
    return await create_user(user)

@protected_router.put("/{user_id}", response_model=UserResponse)
async def update_user_route(user_id: str, user: UserUpdate):
    return await update_user(user_id, user)

@public_router.post("/login", response_model=LoginResponse)
async def login_user_route(user:Login):
    return await login(user)