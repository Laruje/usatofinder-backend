import logging
from urllib.parse import quote_plus

import httpx
from schemas import ListingSchema
from .base import BaseScraper

logger = logging.getLogger(__name__)


class SubitoScraper(BaseScraper):
    platform = "subito"

    async def search(self, query: str) -> list[ListingSchema]:
        url = "https://hades.subito.it/v1/search/items"
        params = {
            "q": query,
            "sort_by": "datedesc",
            "t": "s",
            "start": "0",
            "limit": "30",
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            logger.warning("Subito fetch failed: %s", e)
            return []

        return self._parse(data)

    def _parse(self, data: dict) -> list[ListingSchema]:
        listings: list[ListingSchema] = []

        for ad in data.get("ads", []):
            try:
                title = ad.get("subject", "")
                if not title:
                    continue

                urls = ad.get("urls", {})
                url = urls.get("default", "") or urls.get("mobile", "")
                if not url:
                    continue

                price = None
                for feat in ad.get("features", []):
                    if feat.get("uri") == "/price":
                        values = feat.get("values", [])
                        if values:
                            try:
                                price = float(values[0].get("key", "0"))
                            except (ValueError, TypeError):
                                pass
                        break

                image_url = None
                images = ad.get("images", [])
                if images:
                    img = images[0]
                    cdn = img.get("cdn_base_url", "")
                    base = img.get("base_url", "")
                    image_url = cdn or base

                geo = ad.get("geo", {})
                town = geo.get("town", {}).get("value", "")
                city = geo.get("city", {}).get("value", "")
                location = f"{town}, {city}" if town and city else town or city or None

                ad_id = ad.get("urn", title[:12])

                listings.append(ListingSchema(
                    id=str(ad_id),
                    title=title,
                    price=price,
                    image_url=image_url,
                    url=url,
                    platform=self.platform,
                    location=location,
                ))
            except Exception as e:
                logger.debug("Subito parse error: %s", e)
                continue

        return listings
