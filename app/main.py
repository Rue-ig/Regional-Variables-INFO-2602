# PATH: app/main.py
import uvicorn
import uuid
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.routers import templates, static_files, router, api_router
from app.config import get_settings
from contextlib import asynccontextmanager
from app.database import get_cli_session, create_db_and_tables 
from app.models import Visit


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return RedirectResponse(url="/home")


async def log_visit(request: Request, call_next):
    exclusions = ("/static", "/api", "/robots.txt", "/favicon.ico", "/admin")
    
    if not request.url.path.startswith(exclusions):
        session_id = request.session.get("visit_sid")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["visit_sid"] = session_id

        with get_cli_session() as db:
            try:
                new_visit = Visit(
                    path=request.url.path,
                    session_id=session_id
                )
                db.add(new_visit)
                db.commit()
            except Exception:
                db.rollback()

    return await call_next(request)

app.add_middleware(BaseHTTPMiddleware, dispatch=log_visit)
app.add_middleware(SessionMiddleware, secret_key=get_settings().secret_key)

app.include_router(router)
app.include_router(api_router)
app.mount("/static", static_files, name="static")

@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_redirect_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(request=request, name="401.html")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=get_settings().app_host,
        port=get_settings().app_port,
        reload=get_settings().env.lower() != "production",
    )
