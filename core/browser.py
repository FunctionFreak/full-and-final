import asyncio
import base64
from playwright.async_api import async_playwright

class Browser:
    def __init__(self, browser_settings):
        self.browser_settings = browser_settings
        self.playwright = None
        self.context = None
        self.page = None

    async def initialize(self):
        """
        Initialize Playwright, launch the browser with the specified user data directory,
        and create or get a browser page.
        """
        self.playwright = await async_playwright().start()
        # Launch Chromium using the provided user data directory and headless mode
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_settings.user_data_dir,
            headless=self.browser_settings.headless
        )
        # Use the first available page, or create one if none exist
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        print("Browser initialized.")

    async def get_state(self):
        """
        Retrieve the current state of the browser including URL, title, DOM content,
        and a base64-encoded screenshot.
        """
        if not self.page:
            raise Exception("Browser page is not initialized.")
        
        url = self.page.url
        title = await self.page.title()
        content = await self.page.content()
        # Capture a screenshot and encode it as base64
        screenshot_bytes = await self.page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        state = {
            "url": url,
            "title": title,
            "dom": content,
            "screenshot": screenshot_b64,
        }
        return state

    async def close(self):
        """
        Close the browser context and stop Playwright.
        """
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

# For testing purposes:
if __name__ == "__main__":
    async def main():
        from config.settings import load_settings
        settings = load_settings()
        browser = Browser(settings.browser)
        await browser.initialize()
        state = await browser.get_state()
        print("Current Browser State:", state)
        await browser.close()
    
    asyncio.run(main())
