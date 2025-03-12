import os
import asyncio
import requests

class GroqClient:
    def __init__(self, api_key, model, temperature=0.7, max_tokens=200):
        # Strip any extra whitespace from the API key
        self.api_key = api_key.strip() if api_key else None
        if not self.api_key:
            print("Error: GROQ_API_KEY is missing or empty!")
        else:
            # Print a masked version of the API key for debugging purposes
            masked = self.api_key[:5] + "..." + self.api_key[-5:]
            print(f"Using GROQ_API_KEY: {masked}")
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
            # Run the blocking requests.post call in a thread.
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

# For testing purposes:
if __name__ == "__main__":
    import asyncio
    async def main():
        api_key = os.getenv("GROQ_API_KEY", "")
        model = os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
        client = GroqClient(api_key, model)
        prompt = "What is the capital of France?"
        response = await client.chat_completion(prompt)
        print("AI Response:", response)
    asyncio.run(main())