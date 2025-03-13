import asyncio
import argparse
import logging
import os
from config.settings import load_settings
from terminal.interface import TerminalInterface

# In your logging_config.py or at the start of main.py
import sys

# Configure logging with UTF-8 encoding
class EncodingSafeStreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Replace emoji with text alternatives
            msg = msg.replace("📍", "[STEP]")
            msg = msg.replace("✅", "[SUCCESS]")
            msg = msg.replace("⚠️", "[WARNING]")
            msg = msg.replace("❌", "[FAIL]")
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)

def setup_logging():
    # Clear existing handlers
    root = logging.getLogger()
    root.handlers = []
    
    # Create new handler
    handler = EncodingSafeStreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', 
                                  '%H:%M:%S')
    handler.setFormatter(formatter)
    
    # Configure root logger
    root.addHandler(handler)
    root.setLevel(logging.INFO)

def setup_logging(level=logging.INFO, log_file=None):
    """Configure logging for the application"""
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('playwright').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

async def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Browser Assistant - Control your browser with AI')
    
    parser.add_argument('--headless', action='store_true', 
                        help='Run browser in headless mode')
    parser.add_argument('--vision', action='store_true', 
                        help='Enable vision processing')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--task', type=str,
                        help='Specify a task to run immediately and exit')
    parser.add_argument('--model', type=str,
                        help='Specify the LLM model to use')
    
    args = parser.parse_args()
    
    # Configure logging based on arguments
    log_level = logging.DEBUG if args.debug else logging.INFO
    os.makedirs('logs', exist_ok=True)
    log_file = f'logs/browser_assistant_{int(asyncio.get_event_loop().time())}.log'
    setup_logging(level=log_level, log_file=log_file)
    
    # Load settings
    settings = load_settings()
    
    # Override settings with command line arguments
    if args.headless is not None:
        settings.browser.headless = args.headless
    if args.vision is not None:
        settings.use_vision = args.vision
    if args.model:
        settings.llm.groq_model = args.model
    
    # Create and run the terminal interface
    interface = TerminalInterface(settings)
    
    if args.task:
        # Run a single task and exit
        from core.agent import Agent
        agent = Agent(args.task, settings)
        print(f"Running task: {args.task}")
        history = await agent.run(max_steps=settings.max_steps)
        print("Task completed. Exiting.")
    else:
        # Start interactive mode
        await interface.start()

if __name__ == "__main__":
    asyncio.run(main())