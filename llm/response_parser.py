import json

def parse_response(llm_response):
    """
    Parse the LLM response (expected as a JSON string) to extract action commands.
    
    Expected response format:
    {
        "current_state": { ... },
        "action": [
            {"action_name": { "param1": value1, ... }},
            ...
        ]
    }
    
    Returns:
        A list of action dictionaries if parsing is successful.
    
    Raises:
        ValueError: If parsing fails or the expected format is not met.
    """
    try:
        response_json = json.loads(llm_response)
        actions = response_json.get("action", [])
        if not isinstance(actions, list):
            raise ValueError("The 'action' field is not a list.")
        return actions
    except Exception as e:
        raise ValueError(f"Failed to parse LLM response: {e}")

# For testing purposes:
if __name__ == "__main__":
    # Sample LLM response for testing:
    sample_response = """
    {
        "current_state": {
            "evaluation_previous_goal": "Success",
            "memory": "Visited homepage and identified search box.",
            "next_goal": "Input search query into the search box."
        },
        "action": [
            {"input_text": {"selector": "#search", "text": "Python programming"}},
            {"click": {"selector": "#search-button"}}
        ]
    }
    """
    try:
        actions = parse_response(sample_response)
        print("Parsed Actions:", actions)
    except Exception as e:
        print("Error:", e)
