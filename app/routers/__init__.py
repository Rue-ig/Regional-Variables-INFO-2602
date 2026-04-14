# PATH: app/routers/__init__.py
from pathlib import Path as FilePath
from fastapi import APIRouter, Path as ApiPath
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.utilities.flash import get_flashed_messages
from jinja2 import Environment, FileSystemLoader
from app.config import get_settings

BASE_DIR = FilePath(__file__).resolve().parent.parent

template_env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))
template_env.globals['get_flashed_messages'] = get_flashed_messages
templates = Jinja2Templates(env=template_env)

static_files = StaticFiles(directory=str(BASE_DIR / "static"))

router = APIRouter(
    tags=["Jinja Based Endpoints"],
    include_in_schema=get_settings().env.lower() in ["dev", "development"],
)

api_router = APIRouter(tags=["API Endpoints"], prefix="/api")

from . import (
    index,
    login,
    register,
    admin_home,
    user_home,
    users,
    logout,
    events,
    event_detail,
    reviews,
    photos,
    bookmarks,
    admin_events,
    admin_content,
    admin_import,
)
