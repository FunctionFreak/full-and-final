import os
import asyncio
from groq import Groq

class GroqClient:
    def __init__(self, api_key, model, temperature=0.6, max_tokens=4096, top_p=0.95):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        # Initialize the Groq client using the provided API key
        self.client = Groq(api_key=self.api_key)

    async def chat_completion(self, prompt_message):
        """
        Send a chat completion request to the Groq API using the provided prompt message.
        The request is executed in a separate thread to avoid blocking the event loop.
        """
        messages = [{"role": "user", "content": prompt_message}]
        try:
            # Run the synchronous API call in a thread.
            result = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
                top_p=self.top_p,
                stream=False,
                stop=None
            )
            # Extract and return the message content from the first choice
            return result.choices[0].message.content
        except Exception as e:
            print(f"Error in GroqClient.chat_completion: {e}")
            return ""

# For testing purposes:
if __name__ == "__main__":
    import asyncio
    import os

    async def main():
        # For testing, ensure your environment variable is set (or pass it directly)
        api_key = os.getenv("GROQ_API_KEY", "your_api_key")
        model = os.getenv("GROQ_MODEL", "deepseek-r1-distill-llama-70b")
        client = GroqClient(api_key, model)
        prompt = "Explain the importance of fast language models"
        response = await client.chat_completion(prompt)
        print("LLM Response:", response)

    asyncio.run(main())
