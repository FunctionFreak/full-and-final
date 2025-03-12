import asyncio

class Controller:
    def __init__(self):
        self.registry = {}
        # Register standard browser actions from the actions module.
        from actions.browser_actions import register_browser_actions
        register_browser_actions(self.registry)
        # Optionally, register additional actions (e.g., clipboard actions)
        # from actions.clipboard_actions import register_clipboard_actions
        # register_clipboard_actions(self.registry)

    async def act(self, action, browser):
        """
        Execute a single action on the browser.
        Expected action format: { "action_name": { "param1": value1, ... } }
        """
        if not isinstance(action, dict) or len(action) != 1:
            raise ValueError("Action must be a dict with a single key-value pair.")
        
        action_name, params = list(action.items())[0]
        if action_name not in self.registry:
            raise ValueError(f"Action '{action_name}' is not registered.")
        
        handler = self.registry[action_name]
        # Execute the action handler asynchronously.
        return await handler(params, browser)

    async def multi_act(self, actions, browser):
        """
        Execute multiple actions in sequence.
        If an action returns an 'is_done' flag or an error, break the loop.
        """
        results = []
        for action in actions:
            try:
                result = await self.act(action, browser)
                results.append(result)
                # Check if the action indicates to stop further execution.
                if result.get("is_done") or result.get("error"):
                    break
            except Exception as e:
                results.append({"error": str(e)})
                break
        return results
