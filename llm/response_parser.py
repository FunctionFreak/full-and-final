import json
import re
import logging

logger = logging.getLogger(__name__)

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
        # Clean the response string to handle various formats
        cleaned_response = clean_response_string(llm_response)
        
        # Parse JSON
        response_json = json.loads(cleaned_response)
        
        # Validate the required fields are present
        if "current_state" not in response_json:
            logger.warning("Missing 'current_state' field in LLM response")
            
        if "action" not in response_json:
            logger.error("Missing 'action' field in LLM response")
            raise ValueError("Response must contain an 'action' field")
        
        actions = response_json.get("action", [])
        
        # Validate action format
        if not isinstance(actions, list):
            logger.error("The 'action' field is not a list")
            raise ValueError("The 'action' field must be a list")
        
        # Validate each action
        for i, action in enumerate(actions):
            if not isinstance(action, dict) or len(action) != 1:
                logger.error(f"Invalid action format at index {i}: {action}")
                raise ValueError(f"Each action must be a dictionary with exactly one key (action name)")
                
            # Validate action name and parameters
            action_name = list(action.keys())[0]
            action_params = action[action_name]
            
            if not isinstance(action_params, dict):
                logger.error(f"Invalid parameters for action '{action_name}': {action_params}")
                raise ValueError(f"Parameters for action '{action_name}' must be a dictionary")
        
        return actions
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.debug(f"Raw response: {llm_response}")
        raise ValueError(f"Invalid JSON in LLM response: {e}")
    
    except Exception as e:
        logger.error(f"Error parsing LLM response: {e}")
        raise ValueError(f"Failed to parse LLM response: {e}")

def clean_response_string(response_str):
    """
    Clean the response string to handle various formats that might be returned by the LLM.
    
    Common issues:
    - Response wrapped in markdown code blocks
    - Multiple JSON objects in the response
    - Extra text before or after the JSON
    """
    # If the response is already a dict, just return it as a JSON string
    if isinstance(response_str, dict):
        return json.dumps(response_str)
    
    # Ensure we're working with a string
    if not isinstance(response_str, str):
        response_str = str(response_str)
    
    # Remove markdown code blocks
    if "```json" in response_str:
        # Extract content between ```json and ``` markers
        pattern = r"```json\s*(.*?)\s*```"
        matches = re.findall(pattern, response_str, re.DOTALL)
        if matches:
            response_str = matches[0]
    elif "```" in response_str:
        # Extract content between ``` and ``` markers
        pattern = r"```\s*(.*?)\s*```"
        matches = re.findall(pattern, response_str, re.DOTALL)
        if matches:
            response_str = matches[0]
    
    # Try to find any JSON object in the response
    try:
        # Look for text that seems like JSON (starting with { and ending with })
        pattern = r"\{.*\}"
        matches = re.findall(pattern, response_str, re.DOTALL)
        if matches:
            # Try to parse each match as JSON and use the first valid one
            for match in matches:
                try:
                    json.loads(match)
                    return match
                except:
                    continue
    except:
        pass
    
    # If we couldn't extract a JSON object, return the cleaned response
    return response_str.strip()