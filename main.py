import asyncio
import logging
import os
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Alert
from schemas import AlertCreate, AlertResponse, AlertUpdate, SearchRequest
from services.monitor_service import check_alerts
from services.search_service import search_all

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    interval = int(os.getenv("MONITOR_INTERVAL_MINUTES", "15"))
    scheduler.add_job(lambda: asyncio.ensure_future(check_alerts()), "interval", minutes=interval, id="monitor")
    scheduler.start()
    logging.getLogger(__name__).info("Monitor started (every %d min)", interval)
    yield
    scheduler.shutdown()


app = FastAPI(title="UsatoFinder API", version="1.0.0", lifespan=lifespan)


@app.get("/privacy-policy.html")
async def privacy_policy():
    return FileResponse("privacy-policy.html", media_type="text/html")


@app.post("/api/search")
async def search(request: SearchRequest):
    listings = await search_all(request.query, request.platforms)
    return listings


@app.get("/api/alerts", response_model=list[AlertResponse])
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).all()
    result = []
    for a in alerts:
        result.append(AlertResponse(
            id=a.id, query=a.query, email=a.email, max_price=a.max_price,
            platforms=a.platforms.split(",") if a.platforms else [],
            active=a.active,
        ))
    return result


@app.post("/api/alerts", response_model=AlertResponse)
def create_alert(data: AlertCreate, db: Session = Depends(get_db)):
    alert = Alert(
        query=data.query,
        email=data.email,
        max_price=data.max_price,
        platforms=",".join(data.platforms),
        active=True,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return AlertResponse(
        id=alert.id, query=alert.query, email=alert.email, max_price=alert.max_price,
        platforms=alert.platforms.split(","), active=alert.active,
    )


@app.put("/api/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(alert_id: int, data: AlertUpdate, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if data.active is not None:
        alert.active = data.active
    if data.max_price is not None:
        alert.max_price = data.max_price
    db.commit()
    db.refresh(alert)
    return AlertResponse(
        id=alert.id, query=alert.query, email=alert.email, max_price=alert.max_price,
        platforms=alert.platforms.split(","), active=alert.active,
    )


@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return {"detail": "Alert deleted"}
