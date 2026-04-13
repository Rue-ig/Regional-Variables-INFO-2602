# PATH: app/routers/users.py
from fastapi import Request
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.services.user_service import UserService
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse
from . import api_router

@api_router.get("/users", response_model=list[UserResponse])
async def list_users(request: Request, db: SessionDep, admin: AdminDep):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    return user_service.get_all_users()