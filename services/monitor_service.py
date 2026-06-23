import asyncio
import hashlib
import logging

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Alert, SeenListing
from services.email_service import send_notification
from services.search_service import search_all

logger = logging.getLogger(__name__)


async def check_alerts():
    logger.info("Starting alert check cycle")
    db: Session = SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.active == True).all()
        for alert in alerts:
            await _process_alert(db, alert)
    finally:
        db.close()


async def _process_alert(db: Session, alert: Alert):
    platforms = alert.platforms.split(",") if alert.platforms else ["subito", "ebay", "vinted"]
    try:
        listings = await search_all(alert.query, platforms)
    except Exception as e:
        logger.error("Search failed for alert %d: %s", alert.id, e)
        return

    if alert.max_price is not None:
        listings = [l for l in listings if l.price is not None and l.price <= alert.max_price]

    new_listings = []
    for listing in listings:
        listing_hash = hashlib.md5(f"{listing.url}".encode()).hexdigest()
        existing = db.query(SeenListing).filter(
            SeenListing.alert_id == alert.id,
            SeenListing.listing_hash == listing_hash,
        ).first()
        if not existing:
            new_listings.append(listing)
            db.add(SeenListing(alert_id=alert.id, listing_hash=listing_hash))

    if new_listings:
        db.commit()
        logger.info("Alert %d ('%s'): %d new listings", alert.id, alert.query, len(new_listings))
        await send_notification(alert.email, alert.query, new_listings, alert.max_price)
    else:
        logger.info("Alert %d ('%s'): no new listings", alert.id, alert.query)
