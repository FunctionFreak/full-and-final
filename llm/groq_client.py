import os
import asyncio
import requests

class GroqClient:
    def __init__(self, api_key, model, temperature=0.7, max_tokens=200):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    async def chat_completion(self, prompt_message):
        messages = [
            {"role": "system", "content": "You are an AI assistant for automation."},
            {"role": "user", "content": prompt_message}
        ]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        try:
            response = await asyncio.to_thread(requests.post, self.api_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print("Error:", response.status_code, response.text)
                return ""
        except Exception as e:
            print(f"Error in GroqClient.chat_completion: {e}")
            return ""