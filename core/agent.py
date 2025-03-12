import asyncio
from config.settings import load_settings
from core.browser import Browser
from core.controller import Controller
from core.message_manager import MessageManager
from core.state import AgentState
from llm.groq_client import GroqClient
from vision.vision_processor import VisionProcessor
import json
import logging

logger = logging.getLogger(__name__)

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
        self.n_steps = 0
        self.consecutive_failures = 0
        if settings.use_vision:
            self.vision_processor = VisionProcessor(settings.vision)
        else:
            self.vision_processor = None

    async def run(self, max_steps=100):
        # Initialize the browser (using Playwright)
        await self.browser.initialize()
        
        for step in range(max_steps):
            logger.info(f"\n📍 Step {self.n_steps}")
            self.n_steps += 1
            
            try:
                # Get current browser state
                browser_state = await self.browser.get_state()
                
                # Process vision if enabled
                if self.vision_processor and browser_state.get('screenshot'):
                    vision_results = await self.vision_processor.process(
                        browser_state['screenshot'], browser_state
                    )
                    browser_state['vision'] = vision_results
                
                # Add state to message history
                self.message_manager.add_state_message(browser_state)
                
                # Get prompt for LLM
                prompt_message = self.message_manager.get_latest_message()
                
                # Get next action from LLM
                llm_response = await self.llm_client.chat_completion(prompt_message)
                logger.info(f"LLM Response: {llm_response}")
                
                # Parse actions from LLM response
                try:
                    actions = self.parse_llm_response(llm_response)
                    if not actions:
                        logger.warning("No valid actions received. Continuing to next step.")
                        continue
                        
                    # Execute actions
                    results = await self.controller.multi_act(actions, self.browser)
                    logger.info(f"Action results: {results}")
                    
                    # Update state
                    self.state.update(llm_response, results)
                    self.consecutive_failures = 0
                    
                    # Check if task is done
                    if self.state.is_done():
                        logger.info("✅ Task completed successfully!")
                        break
                except Exception as e:
                    logger.error(f"Error processing LLM response: {e}")
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= 3:
                        logger.error("Too many consecutive failures. Stopping.")
                        break
                
            except Exception as e:
                logger.error(f"Error during step execution: {e}")
                self.consecutive_failures += 1
                if self.consecutive_failures >= 3:
                    logger.error("Too many consecutive failures. Stopping.")
                    break
            
            await asyncio.sleep(0.5)  # Small delay between steps

        return self.state.history

    def parse_llm_response(self, llm_response):
        """
        Parse the LLM JSON response to extract action commands.
        """
        try:
            # Remove markdown formatting if present
            cleaned_response = llm_response
            if "```json" in cleaned_response:
                cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_response:
                cleaned_response = cleaned_response.split("```")[1].split("```")[0].strip()
            
            response_json = json.loads(cleaned_response)
            
            if "current_state" not in response_json or "action" not in response_json:
                logger.error("Response missing required fields: current_state and action")
                return None
            
            actions = response_json.get("action", [])
            if not isinstance(actions, list):
                logger.error("The 'action' field is not a list.")
                return None
                
            return actions
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None