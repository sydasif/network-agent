"""The Proactive Analyzer Agent for comparing network states.

This module implements the Proactive Analyzer agent that compares network device
states over time to detect changes and assess their operational significance.
It uses an LLM to analyze differences between previous and current states,
categorizing them as Critical, Warning, or Informational.
"""
import json
from langchain_groq import ChatGroq
from src.core.config import settings

ANALYSIS_PROMPT = """
You are an expert Senior Network Engineer. Analyze the change in a device's state from the output of the command `{command}` on device `{device_name}`.

**Previous State:**
{previous_state}

**Current State:**
{current_state}

**Analysis Task:**
1. Compare the states and identify key differences.
2. Determine the operational significance: Is this a "Critical" alert (e.g., an interface went down), a "Warning" (e.g., CPU is rising), or just "Informational" (e.g., uptime counter increased)?
3. Provide a concise, one-sentence summary of your finding.

**Respond ONLY in JSON format with the following keys:**
- "change_detected": boolean
- "significance": "Informational", "Warning", or "Critical"
- "summary": "Your one-sentence summary here."
"""

class ProactiveAnalyzer:
    """Analyzes changes in network device states over time.

    The ProactiveAnalyzer compares network device states between different time points
    to detect changes and assess their operational significance (Critical, Warning,
    or Informational). It leverages a Large Language Model to analyze the semantic
    meaning of differences between states.

    Attributes:
        llm: The ChatGroq LLM instance used for analysis.
    """

    def __init__(self, api_key: str):
        """Initializes the ProactiveAnalyzer with an LLM instance.

        Args:
            api_key (str): The Groq API key for accessing the LLM service.
        """
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=settings.groq_model_name,
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}}
        )

    def analyze_change(self, device_name: str, command: str, previous_state: dict, current_state: dict) -> dict:
        """Analyzes changes between previous and current device states.

        Compares two device states and determines if significant changes occurred
        that may require attention. The analysis includes categorizing the change
        by significance level (Critical, Warning, Informational) and providing
        a summary of the findings.

        Args:
            device_name (str): Name of the device being analyzed.
            command (str): The command that generated the state data.
            previous_state (dict): The previous state of the device.
            current_state (dict): The current state of the device.

        Returns:
            dict: A dictionary containing:
                - "change_detected": boolean indicating if changes were detected
                - "significance": significance level ("Informational", "Warning", or "Critical")
                - "summary": one-sentence summary of the change
        """
        if previous_state == current_state:
            return {"change_detected": False, "significance": "Informational", "summary": "No change detected."}

        prompt = ANALYSIS_PROMPT.format(
            device_name=device_name,
            command=command,
            previous_state=json.dumps(previous_state, indent=2),
            current_state=json.dumps(current_state, indent=2)
        )
        response = self.llm.invoke(prompt)
        return json.loads(response.content)