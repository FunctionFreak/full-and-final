import os
import asyncio
import requests
import logging
import json

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key, model, temperature=0.7, max_tokens=200):
        # Strip any extra whitespace from the API key
        self.api_key = api_key.strip() if api_key else None
        if not self.api_key:
            logger.error("Error: GROQ_API_KEY is missing or empty!")
        else:
            # Print a masked version of the API key for debugging purposes
            masked = self.api_key[:5] + "..." + self.api_key[-5:] if len(self.api_key) > 10 else "*****"
            logger.info(f"Using GROQ_API_KEY: {masked}")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    async def chat_completion(self, prompt_message):
        """
        Send a chat completion request to the Groq API and return the response.
        
        Args:
            prompt_message (str): The prompt to send to the LLM
            
        Returns:
            str: The model's response text
        """
        # Format the messages for the API request
        messages = [
            {"role": "system", "content": "You are an AI assistant for browser automation."},
            {"role": "user", "content": prompt_message}
        ]
        
        # Create the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_object"}  # Request JSON output
        }
        
        # Set up headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Make the API request
        try:
            # Run the blocking requests.post call in a thread
            response = await asyncio.to_thread(requests.post, self.api_url, json=payload, headers=headers)
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                response_content = result["choices"][0]["message"]["content"]
                logger.debug(f"Received response: {response_content[:100]}...")
                
                # Validate that the response is valid JSON
                try:
                    json.loads(response_content)
                    return response_content
                except json.JSONDecodeError as e:
                    logger.warning(f"Response is not valid JSON. Attempting to fix: {str(e)}")
                    # Try to clean up the response to make it valid JSON
                    return self._repair_json(response_content)
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return json.dumps({
                    "error": error_msg,
                    "current_state": {
                        "evaluation_previous_goal": "Failed - API error",
                        "memory": "API error occurred while processing the request",
                        "next_goal": "Please retry or check API configuration"
                    },
                    "action": [{"done": {"text": error_msg, "success": False}}]
                })
        except Exception as e:
            error_msg = f"Error in GroqClient.chat_completion: {str(e)}"
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "current_state": {
                    "evaluation_previous_goal": "Failed - connection error",
                    "memory": "Connection error occurred while processing the request",
                    "next_goal": "Please check internet connection and API configuration"
                },
                "action": [{"done": {"text": error_msg, "success": False}}]
            })
    
    def _repair_json(self, json_str):
        """
        Attempt to repair invalid JSON by:
        1. Removing markdown code blocks
        2. Cleaning up common JSON syntax errors
        """
        # Remove markdown formatting
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        # Clean up potential syntax issues
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')
        
        # Try to parse the JSON
        try:
            parsed = json.loads(json_str)
            return json.dumps(parsed)
        except json.JSONDecodeError:
            # Return a fallback JSON if all repair attempts fail
            logger.error(f"Failed to repair JSON: {json_str}")
            return json.dumps({
                "current_state": {
                    "evaluation_previous_goal": "Failed - JSON parsing error",
                    "memory": "Received invalid JSON from LLM",
                    "next_goal": "Try a different action to recover"
                },
                "action": [{"navigate": {"url": "about:blank"}}]
            })