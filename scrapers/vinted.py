import logging

import httpx
from schemas import ListingSchema
from .base import BaseScraper

logger = logging.getLogger(__name__)


class VintedScraper(BaseScraper):
    platform = "vinted"

    async def search(self, query: str) -> list[ListingSchema]:
        try:
            headers = self._get_headers()
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                await client.get("https://www.vinted.it", headers={
                    "User-Agent": headers["User-Agent"],
                    "Accept": "text/html",
                })

                headers["Accept"] = "application/json, text/plain, */*"
                response = await client.get(
                    "https://www.vinted.it/api/v2/catalog/items",
                    params={
                        "search_text": query,
                        "order": "newest_first",
                        "per_page": "30",
                    },
                    headers=headers,
                )
                response.raise_for_status()
                return self._parse(response.json())
        except Exception as e:
            logger.warning("Vinted fetch failed: %s", e)
            return []

    def _parse(self, data: dict) -> list[ListingSchema]:
        listings: list[ListingSchema] = []

        for item in data.get("items", []):
            try:
                item_id = str(item.get("id", ""))
                title = item.get("title", "")
                if not title:
                    continue

                price = None
                price_data = item.get("price")
                if isinstance(price_data, dict):
                    try:
                        price = float(price_data.get("amount", "0"))
                    except (ValueError, TypeError):
                        pass
                elif price_data is not None:
                    try:
                        price = float(str(price_data).replace(",", "."))
                    except ValueError:
                        pass

                photo = item.get("photo", {})
                image_url = photo.get("url") if isinstance(photo, dict) else None

                url = item.get("url", "")
                if url and not url.startswith("http"):
                    url = f"https://www.vinted.it{url}"
                if not url:
                    url = f"https://www.vinted.it/items/{item_id}"

                listings.append(ListingSchema(
                    id=item_id,
                    title=title,
                    price=price,
                    image_url=image_url,
                    url=url,
                    platform=self.platform,
                    location=None,
                ))
            except Exception as e:
                logger.debug("Vinted parse error: %s", e)
                continue

        return listings
