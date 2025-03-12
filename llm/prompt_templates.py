class PromptTemplates:
    @staticmethod
    def format_state_message(state):
        """
        Formats the browser state into a string that can be appended to the system prompt.
        This includes URL, title, a snippet of the DOM, and vision results if available.
        """
        message = (
            f"URL: {state.get('url', '')}\n"
            f"Title: {state.get('title', '')}\n"
            f"DOM (first 300 chars): {state.get('dom', '')[:300]}\n"
        )
        if state.get("vision"):
            message += f"Vision Results: {state.get('vision')}\n"
        return message
