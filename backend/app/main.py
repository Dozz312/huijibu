from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, SessionLocal, engine
from .models import DailyStatus
from .routers import auth, family, status


def reset_daily_statuses():
    """凌晨 4 点重置：删除前一天的所有状态记录，新一天默认全部回家"""
    db = SessionLocal()
    try:
        yesterday = date.today()
        db.query(DailyStatus).filter(DailyStatus.date < yesterday).delete()
        db.commit()
    finally:
        db.close()


scheduler = BackgroundScheduler()
scheduler.add_job(reset_daily_statuses, "cron", hour=settings.RESET_HOUR, minute=0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="回家不 API",
    description="家庭成员回家状态共享服务。默认回家，一键标记不回家。",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(family.router)
app.include_router(status.router)

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
