import asyncio
from config.settings import load_settings
from core.agent import Agent

class TerminalInterface:
    def __init__(self, settings):
        self.settings = settings

    async def start(self):
        print("=== Browser Assistant Terminal Interface ===")
        print("Enter your task (or type 'exit' to quit):")
        while True:
            task = await self.get_user_input(">> ")
            if task.strip().lower() in ['exit', 'quit']:
                print("Exiting the assistant. Goodbye!")
                break

            # Create a new agent instance for each task
            agent = Agent(task, self.settings)
            print(f"Starting task: {task}")
            history = await agent.run(max_steps=self.settings.max_steps)
            print("Task completed. Agent History:")
            for idx, record in enumerate(history, start=1):
                print(f"\n--- Step {idx} ---")
                print("LLM Response:", record.get("llm_response"))
                print("Action Results:", record.get("action_results"))
            print("\nEnter another task or type 'exit' to quit:")

    async def get_user_input(self, prompt):
        """
        Get user input asynchronously by running the built-in input() function in a thread.
        """
        return await asyncio.to_thread(input, prompt)

# For testing purposes:
if __name__ == "__main__":
    async def main():
        settings = load_settings()
        interface = TerminalInterface(settings)
        await interface.start()

    asyncio.run(main())
