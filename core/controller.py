import asyncio
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Controller:
    def __init__(self):
        self.registry = {}
        self._register_actions()

    def _register_actions(self):
        """Register all available browser actions"""
        
        self.registry["navigate"] = self._navigate_action
        self.registry["click_element"] = self._click_element_action
        self.registry["input_text"] = self._input_text_action
        self.registry["go_back"] = self._go_back_action
        self.registry["go_forward"] = self._go_forward_action
        self.registry["scroll"] = self._scroll_action
        self.registry["switch_tab"] = self._switch_tab_action
        self.registry["open_tab"] = self._open_tab_action
        self.registry["close_tab"] = self._close_tab_action
        self.registry["extract_content"] = self._extract_content_action
        self.registry["done"] = self._done_action

    async def _navigate_action(self, params, browser):
        """Navigate to a URL"""
        url = params.get("url")
        if not url:
            return {"error": "URL parameter is required"}
        
        success = await browser.navigate_to(url)
        if success:
            return {"success": True, "message": f"Navigated to {url}"}
        else:
            return {"error": f"Failed to navigate to {url}"}

    async def _click_element_action(self, params, browser):
        """Click an element by index"""
        index = params.get("index")
        if index is None:
            return {"error": "Index parameter is required"}
        
        success = await browser.click_element_by_index(index)
        if success:
            return {"success": True, "message": f"Clicked element with index {index}"}
        else:
            return {"error": f"Failed to click element with index {index}"}

    async def _input_text_action(self, params, browser):
        """Input text into an element by index"""
        index = params.get("index")
        text = params.get("text")
        
        if index is None:
            return {"error": "Index parameter is required"}
        if text is None:
            return {"error": "Text parameter is required"}
            
        success = await browser.input_text(index, text)
        if success:
            return {"success": True, "message": f"Input text into element with index {index}"}
        else:
            return {"error": f"Failed to input text into element with index {index}"}

    async def _go_back_action(self, params, browser):
        """Navigate back in browser history"""
        try:
            await browser.page.go_back()
            return {"success": True, "message": "Navigated back"}
        except Exception as e:
            return {"error": f"Failed to navigate back: {str(e)}"}

    async def _go_forward_action(self, params, browser):
        """Navigate forward in browser history"""
        try:
            await browser.page.go_forward()
            return {"success": True, "message": "Navigated forward"}
        except Exception as e:
            return {"error": f"Failed to navigate forward: {str(e)}"}

    async def _scroll_action(self, params, browser):
        """Scroll the page"""
        direction = params.get("direction", "down")
        amount = params.get("amount", 300)
        
        try:
            if direction == "down":
                await browser.page.evaluate(f"window.scrollBy(0, {amount});")
            elif direction == "up":
                await browser.page.evaluate(f"window.scrollBy(0, -{amount});")
            return {"success": True, "message": f"Scrolled {direction} by {amount} pixels"}
        except Exception as e:
            return {"error": f"Failed to scroll: {str(e)}"}

    async def _switch_tab_action(self, params, browser):
        """Switch to a different tab"""
        page_id = params.get("page_id")
        if page_id is None:
            return {"error": "page_id parameter is required"}
            
        try:
            pages = browser.context.pages
            if page_id < 0 or page_id >= len(pages):
                return {"error": f"Invalid page_id: {page_id}"}
                
            await pages[page_id].bring_to_front()
            browser.page = pages[page_id]
            return {"success": True, "message": f"Switched to tab {page_id}"}
        except Exception as e:
            return {"error": f"Failed to switch tab: {str(e)}"}

    async def _open_tab_action(self, params, browser):
        """Open a new tab with optional URL"""
        url = params.get("url")
        
        try:
            new_page = await browser.context.new_page()
            if url:
                await new_page.goto(url)
            browser.page = new_page
            return {"success": True, "message": f"Opened new tab{' with URL: ' + url if url else ''}"}
        except Exception as e:
            return {"error": f"Failed to open tab: {str(e)}"}

    async def _close_tab_action(self, params, browser):
        """Close the current tab"""
        try:
            await browser.page.close()
            if browser.context.pages:
                browser.page = browser.context.pages[0]
                return {"success": True, "message": "Closed tab and switched to remaining tab"}
            else:
                return {"success": True, "message": "Closed the last tab"}
        except Exception as e:
            return {"error": f"Failed to close tab: {str(e)}"}

    async def _extract_content_action(self, params, browser):
        """Extract content from the current page"""
        selector = params.get("selector")
        
        try:
            if selector:
                content = await browser.page.inner_text(selector)
            else:
                # Extract main content using heuristics
                content = await browser.page.evaluate("""
                    () => {
                        const article = document.querySelector('article');
                        if (article) return article.innerText;
                        
                        const main = document.querySelector('main');
                        if (main) return main.innerText;
                        
                        const body = document.body;
                        return body.innerText;
                    }
                """)
            
            # Trim content to reasonable length
            if len(content) > 5000:
                content = content[:5000] + "...(content truncated)"
                
            return {
                "success": True, 
                "message": "Content extracted", 
                "extracted_content": content,
                "include_in_memory": True
            }
        except Exception as e:
            return {"error": f"Failed to extract content: {str(e)}"}

    async def _done_action(self, params, browser):
        """Mark the task as complete"""
        text = params.get("text", "Task completed")
        success = params.get("success", True)
        
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
            raise ValueError("Action must be a dict with a single key-value pair")
        
        action_name, params = list(action.items())[0]
        if action_name not in self.registry:
            return {"error": f"Unknown action: {action_name}"}
        
        logger.info(f"Executing action: {action_name} with params: {params}")
        handler = self.registry[action_name]
        try:
            result = await handler(params, browser)
            logger.info(f"Action result: {result}")
            return result
        except Exception as e:
            error_msg = f"Error executing {action_name}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    async def multi_act(self, actions, browser):
        """Execute multiple actions in sequence"""
        results = []
        
        for action in actions:
            result = await self.act(action, browser)
            results.append(result)
            
            # Break if action is completed or had an error
            if result.get("is_done") or result.get("error"):
                break
                
            # Small delay between actions to allow page to update
            await asyncio.sleep(0.5)
            
        return results