import hashlib
import logging
import re
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from schemas import ListingSchema
from .base import BaseScraper

logger = logging.getLogger(__name__)

TITLE_NOISE = re.compile(
    r"(?:Nuova inserzione|viene aperta una nuova finestra o scheda)", re.IGNORECASE
)


class EbayItScraper(BaseScraper):
    platform = "ebay"

    async def search(self, query: str) -> list[ListingSchema]:
        url = f"https://www.ebay.it/sch/rss.html?_nkw={quote_plus(query)}&_sop=10&LH_ItemCondition=3000"
        try:
            html = await self._fetch(url)
        except Exception as e:
            logger.warning("eBay fetch failed: %s", e)
            return []

        return self._parse(html)

    def _parse(self, html: str) -> list[ListingSchema]:
        soup = BeautifulSoup(html, "lxml")
        listings: list[ListingSchema] = []

        for card in soup.select("li.s-card"):
            try:
                title_el = card.select_one("span.s-card__title, div.s-card__title")
                if not title_el:
                    continue
                title = TITLE_NOISE.sub("", title_el.get_text(strip=True)).strip()
                if not title or title.lower() in ("shop on ebay", "compra su ebay"):
                    continue

                link_el = card.select_one("a.s-card__link")
                href = link_el.get("href", "") if link_el else ""
                if not href or "ebay" not in href:
                    continue

                price = self._extract_price(card)
                img_el = card.select_one("img[src*='ebayimg']")
                image_url = img_el.get("src") if img_el else None

                listing_id = card.get("data-listingid") or hashlib.md5(href.encode()).hexdigest()[:12]

                listings.append(ListingSchema(
                    id=str(listing_id),
                    title=title,
                    price=price,
                    image_url=image_url,
                    url=href,
                    platform=self.platform,
                    location=None,
                ))
            except Exception as e:
                logger.debug("eBay parse error: %s", e)
                continue

        return listings[:30]

    def _extract_price(self, card) -> float | None:
        price_el = card.select_one("span.s-card__price")
        if not price_el:
            return None
        text = price_el.get_text(strip=True)
        text = text.replace("EUR", "").replace("€", "").replace(".", "").replace(",", ".").strip()
        text = text.split(" a ")[0].split(" fino")[0].strip()
        try:
            return float(text)
        except ValueError:
            return None
