import asyncio
import base64
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class Browser:
    def __init__(self, browser_settings):
        self.browser_settings = browser_settings
        self.playwright = None
        self.context = None
        self.page = None
        self.selector_map = {}  # Map of selectors to their DOM elements

    async def initialize(self):
        """
        Initialize Playwright, launch the browser with the specified user data directory,
        and create or get a browser page.
        """
        logger.info("Initializing browser...")
        self.playwright = await async_playwright().start()
        # Launch Chromium using the provided user data directory and headless mode
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.browser_settings.user_data_dir,
            headless=self.browser_settings.headless,
            args=['--no-sandbox', '--disable-infobars', '--disable-dev-shm-usage']
        )
        # Use the first available page, or create one if none exist
        if self.context.pages:
            self.page = self.context.pages[0]
        else:
            self.page = await self.context.new_page()
        
        # Set viewport size
        await self.page.set_viewport_size({"width": 1280, "height": 800})
        logger.info("Browser initialized successfully.")

    async def get_state(self):
        """
        Retrieve the current state of the browser including URL, title, DOM content,
        and a base64-encoded screenshot, and clickable elements.
        """
        if not self.page:
            raise Exception("Browser page is not initialized.")
        
        # Wait for network idle and any pending animations
        try:
            await self.page.wait_for_load_state("networkidle", timeout=3000)
        except Exception as e:
            logger.warning(f"Wait for network idle timed out: {e}")
        
        url = self.page.url
        title = await self.page.title()
        content = await self.page.content()
        
        # Capture a screenshot
        screenshot_bytes = await self.page.screenshot()
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        
        # Extract clickable elements
        clickable_elements = await self._extract_clickable_elements()
        
        # Get current tabs information
        tabs = await self._get_tabs_info()
        
        state = {
            "url": url,
            "title": title,
            "dom": content,
            "screenshot": screenshot_b64,
            "clickable_elements": clickable_elements,
            "tabs": tabs
        }
        return state
    
    async def _extract_clickable_elements(self):
        """Extract clickable elements from the page with their properties."""
        elements = []
        
        # Use JavaScript to find all potentially interactive elements
        js_code = """
        () => {
            const interactiveElements = [];
            const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'label'];
            const allElements = document.querySelectorAll('*');
            
            let index = 0;
            for (const el of allElements) {
                const tagName = el.tagName.toLowerCase();
                
                // Check if the element is potentially interactive
                const isInteractive = 
                    interactiveTags.includes(tagName) || 
                    el.hasAttribute('role') || 
                    el.hasAttribute('tabindex') || 
                    el.hasAttribute('onclick') ||
                    el.hasAttribute('aria-label');
                
                if (isInteractive) {
                    // Get element properties
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {  // Only visible elements
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden') {
                            interactiveElements.push({
                                index: index++,
                                tagName: tagName,
                                text: el.textContent.trim().substring(0, 100),
                                attributes: {
                                    id: el.id || null,
                                    class: el.className || null,
                                    type: el.type || null,
                                    name: el.name || null,
                                    role: el.getAttribute('role') || null,
                                    'aria-label': el.getAttribute('aria-label') || null,
                                    placeholder: el.getAttribute('placeholder') || null,
                                    value: el.value || null
                                },
                                rect: {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                },
                                xpath: getXPath(el)
                            });
                        }
                    }
                }
            }
            
            // Helper function to get XPath
            function getXPath(element) {
                if (element.id) return `//*[@id="${element.id}"]`;
                
                const paths = [];
                for (; element && element.nodeType === Node.ELEMENT_NODE; element = element.parentNode) {
                    let currentPath = element.tagName.toLowerCase();
                    const siblings = Array.from(element.parentNode?.children || [])
                        .filter(e => e.tagName === element.tagName);
                    
                    if (siblings.length > 1) {
                        const index = siblings.indexOf(element) + 1;
                        currentPath += `[${index}]`;
                    }
                    
                    paths.unshift(currentPath);
                }
                
                return '/' + paths.join('/');
            }
            
            return interactiveElements;
        }
        """
        
        try:
            result = await self.page.evaluate(js_code)
            
            # Update the selector map
            self.selector_map = {}
            for element in result:
                self.selector_map[element['index']] = element
            
            return result
        except Exception as e:
            logger.error(f"Error extracting clickable elements: {e}")
            return []
    
    async def _get_tabs_info(self):
        """Get information about all open tabs."""
        tabs = []
        for i, page in enumerate(self.context.pages):
            tabs.append({
                "page_id": i,
                "url": page.url,
                "title": await page.title()
            })
        return tabs
    
    async def navigate_to(self, url):
        """Navigate to a specific URL."""
        try:
            await self.page.goto(url, wait_until='domcontentloaded')
            logger.info(f"Navigated to: {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False
            
    async def click_element_by_index(self, index):
        """Click an element by its index in the selector map."""
        if index not in self.selector_map:
            logger.error(f"Element with index {index} not found in selector map")
            return False
        
        element = self.selector_map[index]
        try:
            # Try clicking by xpath first
            await self.page.click(f"xpath={element['xpath']}")
            logger.info(f"Clicked element: {element['tagName']} with text: {element['text']}")
            return True
        except Exception as e:
            logger.warning(f"Click by XPath failed, trying alternative methods: {e}")
            try:
                # Try clicking by coordinates
                rect = element['rect']
                x = rect['x'] + rect['width'] / 2
                y = rect['y'] + rect['height'] / 2
                await self.page.mouse.click(x, y)
                logger.info(f"Clicked element by coordinates: {x}, {y}")
                return True
            except Exception as e2:
                logger.error(f"Failed to click element: {e2}")
                return False
    
    async def input_text(self, index, text):
        """Input text into an element by its index."""
        if index not in self.selector_map:
            logger.error(f"Element with index {index} not found in selector map")
            return False
            
        element = self.selector_map[index]
        try:
            await self.page.fill(f"xpath={element['xpath']}", text)
            logger.info(f"Input text into element: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            return False
            
    async def close(self):
        """
        Close the browser context and stop Playwright.
        """
        logger.info("Closing browser...")
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed.")