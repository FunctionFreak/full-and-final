class AgentState:
    def __init__(self):
        # History of steps, each with LLM response and executed action results
        self.history = []
        # Flag to mark if the task is completed
        self._done = False
        # Flag to mark if the task was successful (only valid if done is True)
        self._success = None
        # Final result text from the done action
        self._final_result = None
        # Counter for completed steps
        self.steps_completed = 0

    def update(self, llm_response, action_results):
        """
        Update the state with the latest LLM response and action results.
        If any action result indicates task completion, mark the state as done.
        """
        # Append the current step's data to the history
        self.history.append({
            "llm_response": llm_response,
            "action_results": action_results,
            "step_number": self.steps_completed + 1
        })
        
        self.steps_completed += 1
        
        # Check for any indication that the task is complete.
        for result in action_results:
            if result.get("is_done", False):
                self._done = True
                self._success = result.get("success", False)
                self._final_result = result.get("extracted_content", "Task completed with no details.")
                break

    def is_done(self):
        """Return True if the task is marked as completed."""
        return self._done
    
    def is_successful(self):
        """Return whether the task was completed successfully."""
        return self._success
    
    def get_final_result(self):
        """Get the final result text from the done action."""
        return self._final_result
    
    def get_errors(self):
        """Get all errors from the action results in history."""
        errors = []
        for step in self.history:
            step_errors = []
            for result in step.get("action_results", []):
                if result.get("error"):
                    step_errors.append(result.get("error"))
            errors.append(step_errors)
        return errors
    
    def get_last_error(self):
        """Get the last error from the action results, if any."""
        if not self.history:
            return None
        
        last_step = self.history[-1]
        for result in last_step.get("action_results", []):
            if result.get("error"):
                return result.get("error")
        return None