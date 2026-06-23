from sqlalchemy import Boolean, Column, Float, Integer, String, Text
from database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)
    email = Column(String, nullable=False)
    max_price = Column(Float, nullable=True)
    platforms = Column(String, default="subito,ebay,vinted")
    active = Column(Boolean, default=True)


class SeenListing(Base):
    __tablename__ = "seen_listings"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, nullable=False)
    listing_hash = Column(String, unique=True, nullable=False)
