"""
example web scraper that uses playwright browser pool to efficiently scrape experience data from airbnb.com
Licensed under GPLv3 by <bernardas.alisauskas@gmail.com>
"""
import asyncio
import json
from typing import List
from time import time
from playwrightpool import BrowserPool, BrowserResponse
from parsel import Selector
from loguru import logger as log


class AirbnbScraper:
    url_sitemap = "https://www.airbnb.com/sitemap-master-index.xml.gz"

    def __init__(self, concurrency=3) -> None:
        self.pool = BrowserPool(concurrency, "chromium", {"headless": False})

    async def __aenter__(self):
        await self.pool.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.pool.__aexit__(*args)

    async def parse_experience(self, data: BrowserResponse):
        sel = Selector(data["content"])
        result = {
            "url": data['response'].url,
            "title": sel.css("h1::text").get(),
            "description": sel.xpath(
                '//meta[@property="og:description"]/@content'
            ).get(),
            "review_count": (sel.xpath(
                '//div[@data-section-id="REVIEWS_DEFAULT"]//h2/span/text()'
            ).re("(\d+) reviews") or [0])[0],
            "review_stars": (sel.xpath(
                '//div[@data-section-id="REVIEWS_DEFAULT"]//h2/span/text()'
            ).re("(\d+) out") or [None])[0],
            "location": sel.xpath(
                '//div[@data-section-id="TITLE_DEFAULT"]//a/span/text()'
            ).get(),
        }
        return result

    async def scrape_experiences(self, urls: List[str], batch_size=50):
        while urls:
            batch = urls[:batch_size]
            del urls[:batch_size]
            for data in asyncio.as_completed(
                [self.pool.get_page(url, wait_for_css="h1") for url in batch]
            ):
                data = await data
                yield await self.parse_experience(data)


async def example_run():
    urls = [
        "https://www.airbnb.com/experiences/2496585",
        "https://www.airbnb.com/experiences/2488061",
        "https://www.airbnb.com/experiences/2563542",
        "https://www.airbnb.com/experiences/3010357",
        "https://www.airbnb.com/experiences/2624432",
        "https://www.airbnb.com/experiences/3033250",
    ]
    async with AirbnbScraper() as scraper:
        start = time()
        async for result in scraper.scrape_experiences(urls):
            print(json.dumps(result, ensure_ascii=False))
        log.info(
            f"\nfinished scraping {len(urls)} urls in {time() - start:.1f} seconds"
        )


if __name__ == "__main__":
    asyncio.run(example_run())
