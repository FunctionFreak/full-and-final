async def navigate_action(params, browser):
    """
    Navigate to a given URL.
    Expects params to include:
      - "url": destination URL.
    """
    try:
        url = params.get("url")
        if not url:
            return {"error": "No URL provided for navigation"}
        await browser.page.goto(url)
        return {"success": True, "message": f"Navigated to {url}"}
    except Exception as e:
        return {"error": str(e)}

async def click_action(params, browser):
    """
    Click on an element specified by a CSS selector.
    Expects params to include:
      - "selector": CSS selector of the element to click.
    """
    try:
        selector = params.get("selector")
        if not selector:
            return {"error": "No selector provided for click action"}
        await browser.page.click(selector)
        return {"success": True, "message": f"Clicked element with selector {selector}"}
    except Exception as e:
        return {"error": str(e)}

async def input_text_action(params, browser):
    """
    Input text into an element specified by a CSS selector.
    Expects params to include:
      - "selector": CSS selector of the input element.
      - "text": The text to input.
    """
    try:
        selector = params.get("selector")
        text = params.get("text")
        if not selector or text is None:
            return {"error": "Selector or text not provided for input action"}
        await browser.page.fill(selector, text)
        return {"success": True, "message": f"Input text into element with selector {selector}"}
    except Exception as e:
        return {"error": str(e)}

def register_browser_actions(registry):
    """
    Register browser actions into the provided registry.
    """
    registry["navigate"] = navigate_action
    registry["click"] = click_action
    registry["input_text"] = input_text_action

# For testing purposes:
if __name__ == "__main__":
    registry = {}
    register_browser_actions(registry)
    print("Registered actions:", list(registry.keys()))
