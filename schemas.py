from pydantic import BaseModel, EmailStr


class ListingSchema(BaseModel):
    id: str
    title: str
    price: float | None = None
    currency: str = "EUR"
    image_url: str | None = None
    url: str
    platform: str
    location: str | None = None
    date: str | None = None


class SearchRequest(BaseModel):
    query: str
    platforms: list[str] = ["subito", "ebay", "vinted"]


class AlertCreate(BaseModel):
    query: str
    email: EmailStr
    max_price: float | None = None
    platforms: list[str] = ["subito", "ebay", "vinted"]


class AlertUpdate(BaseModel):
    active: bool | None = None
    max_price: float | None = None


class AlertResponse(BaseModel):
    id: int
    query: str
    email: str
    max_price: float | None
    platforms: list[str]
    active: bool

    class Config:
        from_attributes = True
