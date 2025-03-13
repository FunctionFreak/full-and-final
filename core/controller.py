import asyncio
import logging
import json
import traceback
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self):
        self.registry = {}
        self._register_actions()

    def _register_actions(self):
        """Register all available browser actions"""
        
        # Navigation actions
        self.registry["navigate"] = self._navigate_action
        self.registry["go_back"] = self._go_back_action
        self.registry["go_forward"] = self._go_forward_action
        
        # Element interaction actions
        self.registry["click_element"] = self._click_element_action
        self.registry["input_text"] = self._input_text_action
        self.registry["scroll"] = self._scroll_action
        
        # Tab management actions
        self.registry["switch_tab"] = self._switch_tab_action
        self.registry["open_tab"] = self._open_tab_action
        self.registry["close_tab"] = self._close_tab_action
        
        # Content actions
        self.registry["extract_content"] = self._extract_content_action
        
        # Completion action
        self.registry["done"] = self._done_action
        
        logger.info(f"Registered {len(self.registry)} actions: {', '.join(self.registry.keys())}")

    async def _navigate_action(self, params, browser):
        """Navigate to a URL"""
        url = params.get("url")
        if not url:
            return {"error": "URL parameter is required"}
        
        logger.info(f"Navigating to: {url}")
        try:
            await browser.navigate_to(url)
            # Wait for a moment to ensure page loads before returning
            await asyncio.sleep(0.5)
            return {"success": True, "message": f"Navigated to {url}"}
        except Exception as e:
            error_msg = f"Failed to navigate to {url}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _click_element_action(self, params, browser):
        """Click an element by index"""
        index = params.get("index")
        if index is None:
            return {"error": "Index parameter is required"}
        
        logger.info(f"Clicking element with index: {index}")
        try:
            success = await browser.click_element_by_index(index)
            if success:
                # Wait a moment for any page changes
                await asyncio.sleep(0.5)
                return {"success": True, "message": f"Clicked element with index {index}"}
            else:
                error_msg = f"Failed to click element with index {index}"
                logger.warning(error_msg)
                return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error clicking element with index {index}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _input_text_action(self, params, browser):
        """Input text into an element by index"""
        index = params.get("index")
        text = params.get("text")
        
        if index is None:
            return {"error": "Index parameter is required"}
        if text is None:
            return {"error": "Text parameter is required"}
            
        logger.info(f"Inputting text into element with index: {index}")
        try:
            success = await browser.input_text(index, text)
            if success:
                # Input was successful
                return {"success": True, "message": f"Input text into element with index {index}"}
            else:
                error_msg = f"Failed to input text into element with index {index}"
                logger.warning(error_msg)
                return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error inputting text into element with index {index}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _go_back_action(self, params, browser):
        """Navigate back in browser history"""
        logger.info("Navigating back")
        try:
            await browser.page.go_back()
            # Wait for page to load
            await browser.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(0.5)
            return {"success": True, "message": "Navigated back"}
        except Exception as e:
            error_msg = f"Failed to navigate back: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _go_forward_action(self, params, browser):
        """Navigate forward in browser history"""
        logger.info("Navigating forward")
        try:
            await browser.page.go_forward()
            # Wait for page to load
            await browser.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(0.5)
            return {"success": True, "message": "Navigated forward"}
        except Exception as e:
            error_msg = f"Failed to navigate forward: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _scroll_action(self, params, browser):
        """Scroll the page"""
        direction = params.get("direction", "down")
        amount = params.get("amount", 300)
        
        logger.info(f"Scrolling {direction} by {amount} pixels")
        try:
            if direction == "down":
                await browser.page.evaluate(f"window.scrollBy(0, {amount});")
            elif direction == "up":
                await browser.page.evaluate(f"window.scrollBy(0, -{amount});")
            else:
                return {"error": f"Invalid scroll direction: {direction}. Use 'up' or 'down'."}
                
            await asyncio.sleep(0.3)  # Give time for scroll to complete
            return {"success": True, "message": f"Scrolled {direction} by {amount} pixels"}
        except Exception as e:
            error_msg = f"Failed to scroll: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _switch_tab_action(self, params, browser):
        """Switch to a different tab"""
        page_id = params.get("page_id")
        if page_id is None:
            return {"error": "page_id parameter is required"}
            
        logger.info(f"Switching to tab with page_id: {page_id}")
        try:
            pages = browser.context.pages
            if page_id < 0 or page_id >= len(pages):
                error_msg = f"Invalid page_id: {page_id}. Valid range is 0-{len(pages)-1}."
                logger.warning(error_msg)
                return {"error": error_msg}
                
            await pages[page_id].bring_to_front()
            browser.page = pages[page_id]
            await asyncio.sleep(0.3)  # Brief pause after switching
            return {"success": True, "message": f"Switched to tab {page_id}"}
        except Exception as e:
            error_msg = f"Failed to switch tab: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _open_tab_action(self, params, browser):
        """Open a new tab with optional URL"""
        url = params.get("url")
        
        logger.info(f"Opening new tab{' with URL: ' + url if url else ''}")
        try:
            new_page = await browser.context.new_page()
            if url:
                await new_page.goto(url)
                await new_page.wait_for_load_state("domcontentloaded")
            browser.page = new_page
            await asyncio.sleep(0.5)  # Wait for tab to stabilize
            return {"success": True, "message": f"Opened new tab{' with URL: ' + url if url else ''}"}
        except Exception as e:
            error_msg = f"Failed to open tab: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _close_tab_action(self, params, browser):
        """Close the current tab"""
        logger.info("Closing current tab")
        try:
            await browser.page.close()
            # Switch to another tab if available
            if browser.context.pages:
                browser.page = browser.context.pages[0]
                await asyncio.sleep(0.3)  # Brief pause after switching
                return {"success": True, "message": "Closed tab and switched to remaining tab"}
            else:
                # No tabs left, this is unusual
                logger.warning("Closed the last tab, creating a new blank tab")
                new_page = await browser.context.new_page()
                browser.page = new_page
                return {"success": True, "message": "Closed the last tab, opened new blank tab"}
        except Exception as e:
            error_msg = f"Failed to close tab: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _extract_content_action(self, params, browser):
        """Extract content from the current page"""
        selector = params.get("selector")
        goal = params.get("goal", "Extract page content")
        
        logger.info(f"Extracting content{' with selector: ' + selector if selector else ''}")
        try:
            if selector:
                # Extract content from specific selector
                content = await browser.page.inner_text(selector)
                if not content:
                    logger.warning(f"No content found with selector: {selector}")
                    content = "No content found with the specified selector."
            else:
                # Extract main content using heuristics
                content = await browser.page.evaluate("""
                    () => {
                        // Try to find the main content area
                        const selectors = [
                            'article', 'main', '[role="main"]', 
                            '#content', '.content', '.main-content',
                            'section', '.article'
                        ];
                        
                        // Try each selector in order
                        for (const selector of selectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim().length > 100) {
                                return element.innerText;
                            }
                        }
                        
                        // If no suitable element found, extract from body
                        return document.body.innerText;
                    }
                """)
            
            # Trim content if it's too long
            if content and len(content) > 5000:
                content = content[:5000] + "...(content truncated)"
                
            # Add extracton goal and metadata
            result_text = f"Extracted content for goal: {goal}\n\n{content}"
            
            return {
                "success": True, 
                "message": "Content extracted", 
                "extracted_content": result_text,
                "include_in_memory": True
            }
        except Exception as e:
            error_msg = f"Failed to extract content: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def _done_action(self, params, browser):
        """Mark the task as complete"""
        text = params.get("text", "Task completed")
        success = params.get("success", True)
        
        logger.info(f"Task completed with success={success}")
        
        return {
            "is_done": True,
            "success": success,
            "message": "Task complete",
            "extracted_content": text,
            "include_in_memory": True
        }

    async def act(self, action, browser):
        """Execute a single action on the browser"""
        if not isinstance(action, dict) or len(action) != 1:
            error_msg = "Action must be a dict with a single key-value pair"
            logger.error(error_msg)
            return {"error": error_msg}
        
        action_name, params = list(action.items())[0]
        logger.info(f"Executing action: {action_name} with params: {params}")
        
        if action_name not in self.registry:
            error_msg = f"Unknown action: {action_name}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        handler = self.registry[action_name]
        try:
            # Execute the action handler
            result = await handler(params, browser)
            
            # Log the result
            if "error" in result:
                logger.error(f"Action {action_name} failed: {result['error']}")
            else:
                logger.info(f"Action {action_name} succeeded: {result.get('message', 'No message')}")
                
            return result
        except Exception as e:
            # Capture detailed error information
            error_detail = traceback.format_exc()
            error_msg = f"Error executing {action_name}: {str(e)}"
            logger.error(f"{error_msg}\n{error_detail}")
            return {"error": error_msg}

    async def multi_act(self, actions, browser):
        """Execute multiple actions in sequence"""
        results = []
        
        for action in actions:
            # Execute the action
            result = await self.act(action, browser)
            results.append(result)
            
            # Break if action is completed or had an error
            if result.get("is_done") or result.get("error"):
                break
                
            # Small delay between actions to allow page to update
            await asyncio.sleep(0.5)
            
        return results