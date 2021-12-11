# Playwright Browser Pool

This example illustrates how it's possible to use a pool of browsers to retrieve page urls in a single asynchronous process.

```python
import asyncio


async def run():
    # some example urls
    urls = [
        "https://www.airbnb.com/experiences/2496585",
        "https://www.airbnb.com/experiences/2488061",
        "https://www.airbnb.com/experiences/2563542",
        "https://www.airbnb.com/experiences/3010357",
        "https://www.airbnb.com/experiences/2624432",
        "https://www.airbnb.com/experiences/3033250",
    ]
    # start a browser pool
    async with BrowserPool(pool_size=3, browser_type="chromium", browser_kwargs={"headless": True}) as pool:
        # concurrently execute page retrieval
        for data in asyncio.as_completed(
            [pool.get_page(url) for url in batch]
        ):
            print(data)
            # will print:
            # {
            #   "content": <fully loaded html body>
            #   "response": <initial playwright Response object> (contains response status, headers etc.)
            # }


if __name__ == '__main__':
    asyncio.run(run())
```
