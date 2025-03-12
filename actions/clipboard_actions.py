import pyperclip

async def copy_text_action(params, browser):
    """
    Copy provided text to the clipboard.
    Expects params to include:
      - "text": The text to copy.
    """
    try:
        text = params.get("text")
        if not text:
            return {"error": "No text provided for copy action"}
        pyperclip.copy(text)
        return {"success": True, "message": "Text copied to clipboard."}
    except Exception as e:
        return {"error": str(e)}

async def paste_text_action(params, browser):
    """
    Paste text from the clipboard into an element specified by a CSS selector.
    Expects params to include:
      - "selector": CSS selector of the input element where text will be pasted.
    """
    try:
        selector = params.get("selector")
        if not selector:
            return {"error": "No selector provided for paste action"}
        text = pyperclip.paste()
        # Use Playwright's fill method to paste the text
        await browser.page.fill(selector, text)
        return {"success": True, "message": "Text pasted from clipboard."}
    except Exception as e:
        return {"error": str(e)}

def register_clipboard_actions(registry):
    """
    Register clipboard actions into the provided registry.
    """
    registry["copy_text"] = copy_text_action
    registry["paste_text"] = paste_text_action

# For testing purposes:
if __name__ == "__main__":
    import asyncio

    # Dummy browser object for testing (simulate minimal interface)
    class DummyPage:
        async def fill(self, selector, text):
            print(f"Filling element {selector} with text: {text}")

    class DummyBrowser:
        page = DummyPage()

    async def test_clipboard_actions():
        registry = {}
        register_clipboard_actions(registry)
        browser = DummyBrowser()

        # Test copy_text action
        copy_result = await registry["copy_text"]({"text": "Hello Clipboard"}, browser)
        print("Copy Action Result:", copy_result)

        # Test paste_text action (simulate filling an element)
        paste_result = await registry["paste_text"]({"selector": "#dummy"}, browser)
        print("Paste Action Result:", paste_result)

    asyncio.run(test_clipboard_actions())
