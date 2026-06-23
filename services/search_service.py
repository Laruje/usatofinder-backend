import asyncio
import logging

from scrapers import SubitoScraper, EbayItScraper, VintedScraper
from schemas import ListingSchema

logger = logging.getLogger(__name__)

SCRAPERS = {
    "subito": SubitoScraper(),
    "ebay": EbayItScraper(),
    "vinted": VintedScraper(),
}


async def search_all(query: str, platforms: list[str]) -> list[ListingSchema]:
    selected = [SCRAPERS[p] for p in platforms if p in SCRAPERS]
    tasks = [scraper.search(query) for scraper in selected]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    listings: list[ListingSchema] = []
    for result in results:
        if isinstance(result, list):
            listings.extend(result)
        else:
            logger.warning("Scraper error: %s", result)

    listings.sort(key=lambda x: x.price if x.price is not None else float("inf"))
    return listings
