import asyncio
from playwright.async_api._context_manager import PlaywrightContextManager
from playwright.async_api._generated import Browser, Page, Response
from loguru import logger as log
from typing import Optional, Dict, Literal, Tuple, TypedDict


class BrowserResponse(TypedDict):
    response: Response
    content: str


class BrowserPool:
    def __init__(
        self,
        pool_size=5,
        browser_type: Literal["chromium", "firefox"] = "chromium",
        browser_kwargs: Optional[Dict] = None,
    ) -> None:
        self.pool_size = pool_size
        self.browser_type = browser_type
        self.browser_kwargs = browser_kwargs or {}
        self.pool = {}
        self.pw_manager = None
        self.pw = None

    async def __aenter__(self):
        log.info(
            f"opening browser pool with {self.pool_size} {self.browser_type}({self.browser_kwargs}) browser instances"
        )
        self.pw_manager = PlaywrightContextManager()
        self.pw = await self.pw_manager.__aenter__()
        await asyncio.gather(*[self.start_browser(i) for i in range(self.pool_size)])
        return self

    async def __aexit__(self, *args):
        log.debug("closing browser pool and all attached browsers")
        for browser, page in self.pool.values():
            await browser.close()
        await self.pw_manager.__aexit__(*args)

    async def start_browser(
        self,
        name: str,
    ) -> Tuple[Browser, Page]:
        log.debug(f"starting browser {name}")
        browser = await getattr(self.pw, self.browser_type).launch(
            **self.browser_kwargs
        )
        browser.is_busy = False
        browser.name = name
        context = await browser.new_context()
        page: Page = await context.new_page()
        self.pool[name] = browser, page
        return browser, page

    async def get_browser(self) -> Tuple[Browser, Page]:
        while True:
            for browser, page in self.pool.values():
                if not browser.is_busy:
                    browser.is_busy = True
                    return browser, page
                await asyncio.sleep(
                    0.01
                )  # Note: need to leave open frame here to prevent blocking

    async def get_page(self, url, wait_for_css=None, wait_for_load="domcontentloaded") -> BrowserResponse:
        for i in range(5):
            log.debug(f"{url}: looking for idle browser")
            browser, page = await self.get_browser()
            log.info(f"{url}: using browser {browser.name}")
            try:
                resp = await page.goto(url)
                await page.wait_for_load_state(wait_for_load)
                if wait_for_css:
                    await page.wait_for_selector(wait_for_css)
                content = await page.content()
            except Exception as e:
                # browser went under - restart browser and retry
                log.warning(
                    f"{url}: restarting browser {browser.name} got {e}; retry {i}/5"
                )
                await self.start_browser(browser.name)
                continue
            browser.is_busy = False
            return {
                # final content
                "content": content,
                # doc resource response
                "response": resp,
            }
        raise e
