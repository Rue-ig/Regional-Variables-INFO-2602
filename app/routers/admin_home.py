# PATH: app/routers/admin_home.py
import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta, timezone
from sqlmodel import select, func
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from app.models import Event, Photo, Visit
from app.repositories.user import UserRepository
from app.services.user_service import UserService
from . import router, templates

@router.get("/admin", response_class=HTMLResponse)
async def admin_home_view(request: Request, user: AdminDep, db: SessionDep):
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    total_visitors = db.exec(
        select(func.count(func.distinct(Visit.session_id)))
    ).one()

    stats = {
        "total_events": db.exec(select(func.count()).select_from(Event)).one(),
        "total_visitors": total_visitors,
        "pending_photos": db.exec(
            select(func.count()).select_from(Photo).where(Photo.approved == False)
        ).one(),
        "approved_this_week": db.exec(
            select(func.count()).select_from(Event).where(
                Event.status == 'published',
                Event.updated_at >= one_week_ago
            )
        ).one(),
        "total_reports": 0,
        "pending_reviews": 0,
    }

    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        day = (datetime.now(timezone.utc) - timedelta(days=i)).date()
        count = db.exec(
            select(func.count(Visit.id)).where(
                func.date(Visit.timestamp) == day
            )
        ).one()
        
        chart_labels.append(day.strftime('%a'))
        chart_data.append(count or 0)

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "stats": stats,
            "chart_labels": json.dumps(chart_labels),
            "chart_data": json.dumps(chart_data),
        }
    )


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_view(request: Request, user: AdminDep, db: SessionDep):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    users = user_service.get_all_users()
    
    return templates.TemplateResponse(
        request=request,
        name="/Admin/users.html",
        context={"user": user, "users": users}
    )
