# PATH: app/routers/users.py
from fastapi import Request
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.services.user_service import UserService
from app.repositories.user import UserRepository
from app.schemas.user import UserResponse
from . import router

@router.get("/users", response_model=list[UserResponse])
async def list_users(request: Request, db: SessionDep, admin: AdminDep):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    return user_service.get_all_users()

@router.post("/admin/users/{user_id}/disable")
async def disable_user(
    request: Request,
    user_id: int,
    db: SessionDep,
    admin: AdminDep
):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    success = user_service.disable_user(user_id)
    
    if not success:
        return RedirectResponse(url="/admin/users?error=User+not+found", status_code=303)

    return RedirectResponse(url="/admin/users?message=User+disabled+successfully", status_code=303)

@router.post("/admin/users/{user_id}/enable")
async def enable_user(
    user_id: int, 
    db: SessionDep, 
    admin: AdminDep
):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    if user_service.enable_user(user_id):
        return RedirectResponse(
            url="/admin/users?message=User+access+restored", 
            status_code=303
        )
    
    return RedirectResponse(
        url="/admin/users?error=User+not+found", 
        status_code=303
    )
