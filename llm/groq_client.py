# In llm/groq_client.py

import asyncio
import requests
import json
import logging

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key, model, temperature=0.7, max_tokens=200):
        # Strip any extra whitespace from the API key
        self.api_key = api_key.strip() if api_key else None
        if not self.api_key:
            logger.error("Error: GROQ_API_KEY is missing or empty!")
        else:
            # Print a masked version of the API key for debugging purposes
            masked = self.api_key[:5] + "..." + self.api_key[-5:]
            logger.info(f"Using GROQ_API_KEY: {masked}")
            
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"  # Updated to exact endpoint

    async def chat_completion(self, prompt_message):
        """
        Send a chat completion request to the Groq API following their exact format.
        
        Args:
            prompt_message: The user message to process
            
        Returns:
            String containing the LLM response or error formatted as JSON
        """
        # Format messages exactly as shown in the example
        messages = [
            {"role": "system", "content": "You are an AI assistant for browser automation. Your response must be valid JSON with this format: {\"current_state\": {\"evaluation_previous_goal\": \"...\", \"memory\": \"...\", \"next_goal\": \"...\"}, \"action\": [{\"action_name\": {\"param1\": \"value1\"}}]}"},
            {"role": "user", "content": prompt_message}
        ]
        
        # Construct payload exactly as shown in the example
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # Set headers exactly as shown in the example
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Run the blocking requests.post call in a thread
            response = await asyncio.to_thread(
                requests.post, 
                self.api_url, 
                json=payload, 
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                
                # Return a valid JSON response even in case of API error
                return json.dumps({
                    "current_state": {
                        "evaluation_previous_goal": "Failed - API error",
                        "memory": "API error occurred while processing the request",
                        "next_goal": "Please retry or check API configuration"
                    },
                    "action": [
                        {"done": {"text": error_msg, "success": False}}
                    ]
                })
                
        except Exception as e:
            error_msg = f"Exception in chat_completion: {str(e)}"
            logger.error(error_msg)
            
            # Return a valid JSON response even in case of exception
            return json.dumps({
                "current_state": {
                    "evaluation_previous_goal": "Failed - Exception",
                    "memory": "Exception occurred while processing the request",
                    "next_goal": "Please retry"
                },
                "action": [
                    {"done": {"text": error_msg, "success": False}}
                ]
            })