import asyncio
from config.settings import load_settings
from core.browser import Browser
from core.controller import Controller
from core.message_manager import MessageManager
from core.state import AgentState
from llm.groq_client import GroqClient
from vision.vision_processor import VisionProcessor

class Agent:
    def __init__(self, task, settings):
        self.task = task
        self.settings = settings
        self.state = AgentState()  # Tracks progress and history
        self.browser = Browser(settings.browser)
        self.controller = Controller()
        self.message_manager = MessageManager(task)
        self.llm_client = GroqClient(
        api_key=settings.llm.groq_api_key,
        model=settings.llm.groq_model,
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_completion_tokens,
        )
        if settings.use_vision:
            self.vision_processor = VisionProcessor(settings.vision)
        else:
            self.vision_processor = None

    async def run(self, max_steps=100):
        # Initialize the browser (using Playwright)
        await self.browser.initialize()
        
        for step in range(max_steps):
            print(f"\n--- Step {step+1}/{max_steps} ---")
            # Retrieve current browser state (DOM, URL, screenshot, etc.)
            browser_state = await self.browser.get_state()
            
            # Process vision if enabled and a screenshot is available
            if self.vision_processor and browser_state.get('screenshot'):
                vision_results = await self.vision_processor.process(
                    browser_state['screenshot'], browser_state
                )
                browser_state['vision'] = vision_results
            
            # Add the current state to the message manager (with prompts)
            self.message_manager.add_state_message(browser_state)
            
            # Retrieve the latest message to send as prompt for the LLM
            prompt_message = self.message_manager.get_latest_message()
            
            # Request next action from the LLM via Groq DeepSeek
            llm_response = await self.llm_client.chat_completion(prompt_message)
            print("LLM Response:", llm_response)
            
            # Parse the LLM response to extract action commands
            actions = self.parse_llm_response(llm_response)
            if not actions:
                print("No valid actions received. Terminating agent loop.")
                break
            
            # Execute the actions using the controller
            results = await self.controller.multi_act(actions, self.browser)
            print("Action results:", results)
            
            # Update agent state based on the LLM response and executed actions
            self.state.update(llm_response, results)
            
            # Check if task is marked as completed
            if self.state.is_done():
                print("Task completed successfully!")
                break

            await asyncio.sleep(0.1)  # Small delay between steps

        return self.state.history

    def parse_llm_response(self, llm_response):
        """
        Parse the LLM JSON response to extract action commands.
        Uses the response_parser from the llm module.
        """
        from llm.response_parser import parse_response
        try:
            actions = parse_response(llm_response)
            return actions
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return None

# For testing purposes:
if __name__ == "__main__":
    async def main():
        settings = load_settings()
        # For example, task could be: "Go to google.com and search for Python programming"
        task = "Go to google.com and search for Python programming"
        agent = Agent(task, settings)
        history = await agent.run(max_steps=10)
        print("Agent History:", history)
    
    asyncio.run(main())
