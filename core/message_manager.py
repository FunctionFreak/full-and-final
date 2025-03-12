import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class MessageManager:
    def __init__(self, task):
        self.task = task
        self.messages = []
        self.history = []  # Store browser state history
        self.load_prompts()

    def load_prompts(self):
        """Load prompt templates from files"""
        base_dir = Path(__file__).parent.parent / "prompts"
        system_prompt_path = base_dir / "system_prompt.md"
        
        if system_prompt_path.exists():
            self.system_prompt = system_prompt_path.read_text(encoding="utf-8")
        else:
            # Default system prompt if file not found
            self.system_prompt = """You are an AI agent designed to automate browser tasks. Your goal is to accomplish the task following the rules.

**Input Format:**
- Task description
- Current URL
- Page title
- A list of interactive elements on the page
- Vision analysis (if available)

**Response Format:**
Your response must be a valid JSON object with the following structure:

```json
{
  "current_state": {
    "evaluation_previous_goal": "Success|Failed|Unknown - A brief evaluation of the previous step",
    "memory": "A summary of what has been done so far",
    "next_goal": "A description of the next immediate action"
  },
  "action": [
    {"action_name": {"param1": "value1", ...}}
  ]
}
```"""
        
        # Add task information to the system prompt
        self.system_prompt += f"\n\nYour task: {self.task}\n\n"
        
        # Add the first system message to the conversation
        self.messages.append({"role": "system", "content": self.system_prompt})
        
        # Add available actions documentation
        actions_doc = """
**Available Actions:**

1. **navigate**: Go to a specific URL
   ```json
   {"navigate": {"url": "https://example.com"}}
2. click_element: Click on an element by its index
    ```json
   {"click_element": {"index": 5}}
3. input_text: Type text into an element by its index
    ```json
   {"input_text": {"index": 3, "text": "hello world"}}
4. go_back: Navigate back in the browser history
    ```json
   {"go_back": {}}
5. go_forward: Navigate forward in the browser history
    ```json
   {"go_forward": {}}
6. scroll: Scroll the page by amount of pixels
    ```json
   {"scroll": {"direction": "down", "amount": 300}}
7. switch_tab: Switch to another tab by its ID
    ```json
   {"switch_tab": {"page_id": 1}}
8. open_tab: Open a new tab with optional URL
    ```json
   {"open_tab": {"url": "https://example.com"}}
9. close_tab: Close the current tab
    ```json
   {"close_tab": {}}
10. extract_content: Extract content from the page
    ```json
   {"extract_content": {"selector": "article"}}
11. done: Mark the task as complete with success or failure
    ```json
   {"done": {"text": "Task completed successfully", "success": true}}

"""
        self.messages[0]["content"] += actions_doc

    def add_state_message(self, state):
        """
        Format the browser state and add it to the message history.
        """
        # Store the state in history
        self.history.append(state)
        
        # Format the browser state as a message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format clickable elements in a readable way
        elements_text = self._format_clickable_elements(state.get("clickable_elements", []))
        
        # Format tabs information
        tabs_text = self._format_tabs(state.get("tabs", []))
        
        # Compile the full state message
        state_message = f"""
Current State at {timestamp}:
URL: {state.get('url', 'N/A')}
Title: {state.get('title', 'N/A')}
Available Tabs:
{tabs_text}
Interactive Elements:
{elements_text}
"""
        # Add vision analysis if available
        if state.get("vision"):
            vision_summary = self._format_vision_results(state["vision"])
            state_message += f"\nVision Analysis:\n{vision_summary}\n"
        
        # Add to messages
        self.messages.append({"role": "user", "content": state_message})
        logger.info(f"Added state message with {len(state.get('clickable_elements', []))} elements")

    def _format_clickable_elements(self, elements):
        """Format clickable elements in a readable format for the LLM"""
        if not elements:
            return "No interactive elements found."
            
        formatted_elements = []
        for element in elements:
            # Get basic element info
            index = element.get("index")
            tag = element.get("tagName", "unknown")
            text = element.get("text", "").strip()
            
            # Get important attributes
            attrs = element.get("attributes", {})
            important_attrs = []
            for attr_name in ["id", "role", "aria-label", "type", "placeholder", "name"]:
                if attrs.get(attr_name):
                    important_attrs.append(f'{attr_name}="{attrs[attr_name]}"')
            
            # Format the element string
            element_str = f"[{index}]<{tag}"
            if important_attrs:
                element_str += f" {' '.join(important_attrs)}"
                
            if text:
                text = text[:50] + ("..." if len(text) > 50 else "")
                element_str += f">{text}</{tag}>"
            else:
                element_str += " />"
                
            formatted_elements.append(element_str)
            
        return "\n".join(formatted_elements)

    def _format_tabs(self, tabs):
        """Format tabs information"""
        if not tabs:
            return "No tabs available."
            
        formatted_tabs = []
        for tab in tabs:
            tab_str = f"Tab {tab.get('page_id')}: {tab.get('title', 'Untitled')} - {tab.get('url', 'No URL')}"
            formatted_tabs.append(tab_str)
            
        return "\n".join(formatted_tabs)

    def _format_vision_results(self, vision_results):
        """Format vision analysis results"""
        formatted_result = ""
        
        # Format object detections
        detections = vision_results.get("detections", [])
        if detections:
            formatted_result += "Detected Objects:\n"
            for i, detection in enumerate(detections[:10]):  # Limit to first 10 for brevity
                cls = detection.get("class", "unknown")
                conf = detection.get("confidence", 0)
                bbox = detection.get("bbox", [0, 0, 0, 0])
                formatted_result += f"- {cls} (confidence: {conf:.2f}) at position: [{bbox[0]:.0f}, {bbox[1]:.0f}, {bbox[2]:.0f}, {bbox[3]:.0f}]\n"
            
            if len(detections) > 10:
                formatted_result += f"... and {len(detections) - 10} more objects\n"
        
        # Format OCR text regions
        text_regions = vision_results.get("text_regions", [])
        if text_regions:
            formatted_result += "\nDetected Text:\n"
            for i, region in enumerate(text_regions[:15]):  # Limit to first 15 for brevity
                text = region.get("text", "")
                conf = region.get("confidence", 0)
                formatted_result += f"- '{text}' (confidence: {conf:.2f})\n"
                
            if len(text_regions) > 15:
                formatted_result += f"... and {len(text_regions) - 15} more text regions\n"
                
        return formatted_result if formatted_result else "No vision analysis available."

    def add_llm_response(self, response):
        """Add LLM response to the conversation history"""
        try:
            # Clean up the response for better display
            if isinstance(response, str):
                # Try to parse the response as JSON for better display
                try:
                    json_response = json.loads(response)
                    # Format the assistant message with the parsed JSON
                    formatted_response = "```json\n" + json.dumps(json_response, indent=2) + "\n```"
                except:
                    # If not valid JSON, use as is
                    formatted_response = response
            else:
                # If not a string, convert to string
                formatted_response = str(response)
                
            self.messages.append({"role": "assistant", "content": formatted_response})
            logger.info("Added LLM response to message history")
        except Exception as e:
            logger.error(f"Failed to add LLM response: {e}")

    def get_latest_message(self):
        """Get the latest state message for the LLM"""
        # For simplicity, we'll use the whole conversation history
        # In a production environment, you might want to limit this based on token count
        
        # Format the messages for the LLM in a proper conversational format
        formatted_conversation = ""
        
        # Always include system prompt
        formatted_conversation += self.messages[0]["content"] + "\n\n"
        
        # Add the conversation history
        # Skip the first message (system prompt) since we already included it
        for msg in self.messages[1:]:
            role = msg["role"]
            content = msg["content"]
            
            if role == "user":
                formatted_conversation += "User message:\n"
            elif role == "assistant":
                formatted_conversation += "Assistant response:\n"
                
            formatted_conversation += content + "\n\n"
            
        return formatted_conversation

    def get_message_history(self):
        """Get the full message history"""
        return self.messages