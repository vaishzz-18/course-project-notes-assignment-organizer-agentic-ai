from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import init_db, get_db
from api.routes import auth, courses, notes, assignments, submissions, grades, milestones, audit, agents, lab1, lab2, lab3, lab4, lab5, lab6, lab7, lab8, lab9, lab10, lab11, lab12, lab13, lab14, lab15
from services.health_check_service import HealthCheckService
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.NOTES_DIR.mkdir(parents=True, exist_ok=True)
    settings.SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

cors_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(notes.router)
app.include_router(assignments.router)
app.include_router(submissions.router)
app.include_router(grades.router)
app.include_router(milestones.router)
app.include_router(audit.router)
app.include_router(agents.router)
app.include_router(lab1.router)
app.include_router(lab2.router)
app.include_router(lab3.router)
app.include_router(lab4.router)
app.include_router(lab5.router)
app.include_router(lab6.router)
app.include_router(lab7.router)
app.include_router(lab8.router)
app.include_router(lab9.router)
app.include_router(lab10.router)
app.include_router(lab11.router)
app.include_router(lab12.router)
app.include_router(lab13.router)
app.include_router(lab14.router)
app.include_router(lab15.router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Simple liveness probe for orchestrators and load balancers."""
    return {"status": "ok"}


@app.get("/health/detailed")
async def health_detailed(db: AsyncSession = Depends(get_db)):
    """Comprehensive readiness probe inspecting database, MCP server, and storage."""
    svc = HealthCheckService(db)
    return await svc.get_full_report()
