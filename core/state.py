class AgentState:
    def __init__(self):
        # History of steps, each with LLM response and executed action results
        self.history = []
        # Flag to mark if the task is completed
        self._done = False

    def update(self, llm_response, action_results):
        """
        Update the state with the latest LLM response and action results.
        If any action result indicates task completion, mark the state as done.
        """
        # Append the current step's data to the history
        self.history.append({
            "llm_response": llm_response,
            "action_results": action_results
        })
        
        # Check for any indication that the task is complete.
        # For example, if any action result has 'is_done' set to True.
        for result in action_results:
            if result.get("is_done", False):
                self._done = True
                break

    def is_done(self):
        """Return True if the task is marked as completed."""
        return self._done
