# PATH: app/routers/admin_home.py
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
async def admin_home_view(
    request: Request,
    user: AdminDep,
    db: SessionDep
):
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    stats = {
        "total_events": db.exec(select(func.count()).select_from(Event)).one(),
        "pending_photos": db.exec(select(func.count()).select_from(Photo).where(Photo.approved == False)).one(),
        "approved_this_week": db.exec(
            select(func.count()).select_from(Event).where(
                Event.status == 'published', 
                Event.updated_at >= one_week_ago
            )
        ).one(),
        "site_visitors": db.exec(select(func.count()).select_from(Visit).where(Visit.timestamp >= one_week_ago)).one(),
        "pending_reviews": 0,
        "new_events": 0
    }

    daily_visits = db.exec(
        select(
            func.date(Visit.timestamp).label('date'),
            func.count(Visit.id).label('count')
        ).where(Visit.timestamp >= one_week_ago)
         .group_by(func.date(Visit.timestamp))
         .order_by('date')
    ).all()

    chart_labels = []
    chart_data = []
    
    for row in daily_visits:
        date_obj = datetime.strptime(row[0], '%Y-%m-%d') if isinstance(row[0], str) else row[0]
        chart_labels.append(date_obj.strftime('%a'))
        chart_data.append(row[1])

    return templates.TemplateResponse(
        request=request, 
        name="admin.html",
        context={
            "user": user,
            "stats": stats,
            "chart_labels": chart_labels,
            "chart_data": chart_data
        }
    )

@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_view(
    request: Request,
    user: AdminDep,
    db: SessionDep
):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    users = user_service.get_all_users()
    
    return templates.TemplateResponse(
        request=request,
        name="/Admin/users.html",
        context={
            "user": user,
            "users": users
        }
    )