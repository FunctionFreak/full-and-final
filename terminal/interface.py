import asyncio
import logging
import time
import os
from config.settings import load_settings
from core.agent import Agent

logger = logging.getLogger(__name__)

class TerminalInterface:
    def __init__(self, settings):
        self.settings = settings
        self.setup_logging()

    def setup_logging(self):
        """Setup terminal-friendly logging"""
        # Create a custom formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                     datefmt='%H:%M:%S')
        
        # Configure the root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # Create console handler
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root_logger.addHandler(console)
        
        # Create file handler if logs directory exists or can be created
        try:
            os.makedirs("logs", exist_ok=True)
            file_handler = logging.FileHandler(f"logs/browser_agent_{time.strftime('%Y%m%d_%H%M%S')}.log")
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up log file: {e}")

    async def start(self):
        """Start the terminal interface for the agent"""
        self._print_banner()
        
        print("Enter your task (or type 'exit' to quit):")
        while True:
            task = await self._get_user_input(">> ")
            if task.strip().lower() in ['exit', 'quit']:
                print("Exiting the assistant. Goodbye!")
                break

            # Run the agent with a progress display
            await self._run_agent_with_progress(task)
            
            print("\nEnter another task or type 'exit' to quit:")

    def _print_banner(self):
        """Display a welcome banner"""
        banner = """
╔══════════════════════════════════════════════════════╗
║                                                      ║
║        🌐 Browser Assistant Terminal Interface        ║
║                                                      ║
║  Powered by Groq DeepSeek + Playwright + YOLOv8      ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
        """
        print(banner)
        print(f"Model: {self.settings.llm.groq_model}")
        print(f"Vision: {'Enabled' if self.settings.use_vision else 'Disabled'}")
        print(f"Browser: {'Headless' if self.settings.browser.headless else 'Visible'}")
        print("=" * 60)

    async def _get_user_input(self, prompt):
        """Get user input asynchronously by running the built-in input() function in a thread."""
        return await asyncio.to_thread(input, prompt)

    async def _run_agent_with_progress(self, task):
        """Run the agent with a progress display"""
        # Create a new agent instance for each task
        agent = Agent(task, self.settings)
        print(f"\n🔄 Starting task: {task}")
        
        # Progress indicators
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        spinner_idx = 0
        
        # Start agent in background task
        agent_task = asyncio.create_task(agent.run(max_steps=self.settings.max_steps))
        
        # Show progress while agent runs
        try:
            while not agent_task.done():
                print(f"\r{spinner[spinner_idx]} Agent working...", end="", flush=True)
                spinner_idx = (spinner_idx + 1) % len(spinner)
                await asyncio.sleep(0.1)
            
            # Clear the spinner line
            print("\r" + " " * 30 + "\r", end="", flush=True)
            
            # Get agent result
            history = await agent_task
            
            # Display the results
            self._display_agent_results(agent, history)
            
        except Exception as e:
            print(f"\n❌ Error occurred while running agent: {str(e)}")
            logger.error(f"Agent execution error: {e}", exc_info=True)
        finally:
            # Make sure to close browser resources
            try:
                await agent.browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")

    def _display_agent_results(self, agent, history):
        """Display the agent execution results"""
        success = agent.state.is_successful()
        done = agent.state.is_done()
        final_result = agent.state.get_final_result()
        error = agent.state.get_last_error()
        
        print("\n" + "=" * 60)
        
        if done:
            if success:
                print("✅ Task completed successfully!")
            else:
                print("⚠️ Task completed but with issues.")
        else:
            print("❌ Task did not complete successfully.")
        
        if final_result:
            print("\n📋 Result:")
            print("-" * 60)
            print(final_result)
            print("-" * 60)
        
        if error:
            print("\n⚠️ Last error:")
            print(error)
        
        print(f"\n🔢 Steps completed: {len(history)}")
        print("=" * 60)
        
        # Ask if user wants to see detailed history
        print("\nWould you like to see the detailed execution history? (y/n)")
        show_history = input("> ").strip().lower()
        if show_history == 'y':
            self._display_detailed_history(history)

    def _display_detailed_history(self, history):
        """Display detailed execution history"""
        print("\n📜 DETAILED EXECUTION HISTORY")
        print("=" * 60)
        
        for idx, record in enumerate(history, start=1):
            print(f"\n--- Step {idx} ---")
            
            # Show LLM response
            llm_response = record.get("llm_response", "No LLM response")
            if isinstance(llm_response, str) and len(llm_response) > 500:
                llm_response = llm_response[:500] + "... (truncated)"
            print(f"LLM Response: {llm_response}")
            
            # Show action results
            action_results = record.get("action_results", [])
            print(f"Actions ({len(action_results)}):")
            for i, result in enumerate(action_results):
                success = "✅" if result.get("success", False) and not result.get("error") else "❌"
                action_type = next(iter(result.keys())) if isinstance(result, dict) else "unknown"
                message = result.get("message", "No message")
                error = result.get("error", "")
                
                print(f"  {success} Action {i+1}: {action_type}")
                if message:
                    print(f"     Message: {message}")
                if error:
                    print(f"     Error: {error}")
            
            print("-" * 60)

# For testing purposes:
if __name__ == "__main__":
    async def main():
        settings = load_settings()
        interface = TerminalInterface(settings)
        await interface.start()

    asyncio.run(main())