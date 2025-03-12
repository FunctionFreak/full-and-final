import json
from datetime import datetime
from pathlib import Path

class MessageManager:
    def __init__(self, task):
        self.task = task
        self.messages = []
        self.load_prompts()

    def load_prompts(self):
        # Load prompt files from the prompts directory
        base_dir = Path(__file__).parent.parent / "prompts"
        system_prompt_path = base_dir / "system_prompt.md"
        message_template_path = base_dir / "custom_message_template.md"

        if system_prompt_path.exists():
            self.system_prompt = system_prompt_path.read_text(encoding="utf-8")
        else:
            self.system_prompt = "Default system prompt not found."

        if message_template_path.exists():
            self.message_template = message_template_path.read_text(encoding="utf-8")
        else:
            # Default template if the file is missing
            self.message_template = (
                "Timestamp: {timestamp}\n"
                "URL: {url}\n"
                "Title: {title}\n"
                "DOM Snippet: {dom}\n"
                "Vision Results: {vision}\n"
            )

    def add_state_message(self, state):
        """
        Format the browser state using the custom message template and add it to the message history.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = self.message_template.format(
            timestamp=timestamp,
            url=state.get("url", ""),
            title=state.get("title", ""),
            dom=state.get("dom", "N/A")[:500],  # Limit DOM content for brevity
            vision=state.get("vision", "N/A")
        )
        # Here, we use the role "user" for state messages.
        self.messages.append({"role": "user", "content": formatted_message})

    def add_custom_message(self, role, content):
        """
        Add a custom message with the given role (e.g., system, user, assistant).
        """
        self.messages.append({"role": role, "content": content})

    def get_latest_message(self):
        """
        Combine the system prompt and all message history into one final prompt.
        """
        conversation = "\n".join([msg["content"] for msg in self.messages])
        final_prompt = f"{self.system_prompt}\n{conversation}"
        return final_prompt

    def get_message_history(self):
        return self.messages

# For testing the MessageManager functionality
if __name__ == "__main__":
    dummy_state = {
        "url": "https://example.com",
        "title": "Example Page",
        "dom": "<html><body>Example Content...</body></html>",
        "vision": "No vision data"
    }
    mm = MessageManager("Test Task")
    mm.add_state_message(dummy_state)
    mm.add_custom_message("assistant", "This is a test assistant message.")
    prompt = mm.get_latest_message()
    print("Final Prompt:\n", prompt)
