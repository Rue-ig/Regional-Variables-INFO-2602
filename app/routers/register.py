from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request, status, Form
from app.dependencies import SessionDep
from app.services.auth_service import AuthService
from app.repositories.user import UserRepository
from app.utilities.flash import flash
from . import router, templates

@router.get("/register", response_class=HTMLResponse)
async def register_view(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="register.html",
    )

@router.post('/register', response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
def signup_user(request:Request, db:SessionDep, 
    username: str = Form(),
    email: str = Form(),
    password: str = Form(),
):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    
    try:
        user = auth_service.register_user(username, email, password)
        flash(request, f"Welcome {user.username}! Registration completed! Sign in now!")
        
        return RedirectResponse(url=request.url_for("login_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    except Exception as e:
        flash(request, "Username or email already exists", "danger")
        
        return RedirectResponse(url=request.url_for("register_view"), status_code=status.HTTP_303_SEE_OTHER)
