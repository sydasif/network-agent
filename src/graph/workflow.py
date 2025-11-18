"""The core LangGraph workflow for the multi-agent system.

This module implements the main workflow for the AI network agent using LangGraph.
The workflow orchestrates multiple agents including a Planner agent (which creates
execution plans), Tool Executor (which executes the plans), and a Generator agent
(which synthesizes responses). The workflow processes user intents through this
multi-agent system to generate appropriate responses.
"""

import json
import re
from typing import List, TypedDict
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from src.agents.planner import get_planner_prompt
from src.agents.executor import tool_executor
from src.core.models import UserIntent
from src.core.config import settings


class AgentState(TypedDict):
    """Defines the state structure for the LangGraph workflow.

    This TypedDict defines the structure of the state that flows through the
    LangGraph workflow. It contains all the information needed for the agents
    to process user requests and maintain context.

    Attributes:
        input (str): Raw user query
        chat_history (List[BaseMessage]): The conversation history.
        structured_intent: The structured intent from NLP preprocessing
        plan (List[dict]): The execution plan created by the planner agent.
        tool_results (List[any]): Results from executing the plan.
        response (str): The final synthesized response to the user.
    """

    input: str  # Raw user query
    chat_history: List[BaseMessage]
    structured_intent: UserIntent  # The structured output
    plan: List[dict]
    tool_results: List[dict]
    response: str


class NetworkWorkflow:
    """Orchestrates the multi-agent workflow for processing network queries.

    The NetworkWorkflow class sets up and manages a LangGraph workflow that
    processes user intents through a sequence of agents: Planner, Executor,
    and Generator. It handles the entire flow from structured intent to final response.

    Attributes:
        llm: The ChatGroq LLM instance used by the workflow.
        graph: The compiled LangGraph workflow.
    """

    def __init__(self, api_key: str):
        """Initializes the NetworkWorkflow with an LLM instance.

        Sets up the LLM and compiles the LangGraph workflow.

        Args:
            api_key (str): The Groq API key for accessing the LLM service.
        """
        self.llm = ChatGroq(
            groq_api_key=api_key, model_name=settings.groq_model_name, temperature=0
        )

        # This creates a specialized LLM that ONLY outputs your Pydantic model.
        # It handles the prompt, the schema, and the validation automatically.
        self.intent_classifier = self.llm.with_structured_output(UserIntent)

        self.graph = self._build_graph()

    def _build_graph(self):
        """Builds the LangGraph workflow with preprocessor, planner, executor, and generator nodes.

        Creates a state graph with four nodes that process the request in sequence:
        1. Preprocessor node classifies intent and extracts entities
        2. Planner node creates an execution plan
        3. Executor node executes the plan
        4. Generator node synthesizes the final response

        Returns:
            The compiled LangGraph workflow.
        """
        workflow = StateGraph(AgentState)
        workflow.add_node("preprocessor", self.preprocessor_node)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("executor", self.executor_node)
        workflow.add_node("generator", self.generator_node)

        workflow.set_entry_point("preprocessor")  # Start here

        workflow.add_edge("preprocessor", "planner")

        # Conditional edge from planner - if there's a response, go directly to END, otherwise proceed with execution
        workflow.add_conditional_edges(
            "planner", self._should_continue, {"continue": "executor", "end": END}
        )

        workflow.add_edge("executor", "generator")
        workflow.add_edge("generator", END)
        return workflow.compile()

    def _should_continue(self, state):
        """Determine whether to continue with executor/generator nodes or end early."""
        # If there's already a response in the state, we should end early
        if state.get("response"):
            return "end"
        return "continue"

    def preprocessor_node(self, state: AgentState):
        """Classify intent using the structured LLM."""
        print(f"🔍 Analyzing: {state['input']}")

        query = state["input"].strip().lower()

        # Handle simple cases before attempting structured output
        if query in [
            "hi",
            "hello",
            "hey",
            "greetings",
            "good morning",
            "good afternoon",
            "good evening",
            "good night",
        ]:
            intent = self._create_greeting_intent()
            return {
                "structured_intent": intent,
                "response": "Hello! I'm your network assistant. How can I help?",
                "plan": [],
            }

        # Attempt to classify the intent using the LLM, with fallback processing
        intent = self._classify_intent_or_fallback(query, state["input"])

        # Quick routing checks based on intent - return early for simple queries to avoid planner issues
        if intent.intent == "greeting":
            return {
                "structured_intent": intent,
                "response": "Hello! I'm your network assistant. How can I help?",
                "plan": [],
            }
        if intent.is_ambiguous:
            return {
                "structured_intent": intent,
                "response": "Could you please specify which device you are referring to?",
                "plan": [],
            }

        return {"structured_intent": intent}

    def _create_greeting_intent(self) -> UserIntent:
        """Create a greeting intent with empty entities."""
        from src.core.models import ExtractedEntities

        return UserIntent(
            intent="greeting", entities=ExtractedEntities(), is_ambiguous=False
        )

    def _classify_intent_or_fallback(
        self, query: str, original_input: str
    ) -> UserIntent:
        """Attempt to classify the intent using the LLM, with fallback to basic parsing.

        Args:
            query: The normalized query string
            original_input: The original input string for pattern matching

        Returns:
            The classified UserIntent
        """
        try:
            # One line to do all the NLP work
            return self.intent_classifier.invoke(original_input)
        except Exception as e:
            # If the structured output fails, attempt to extract basic information manually
            print(f"⚠️ Structured output failed, using fallback: {e}")
            # For simple cases, create a default intent
            from src.core.models import ExtractedEntities

            intent = UserIntent(
                intent="unknown", entities=ExtractedEntities(), is_ambiguous=False
            )

            # Try to detect basic intent patterns
            if any(word in query for word in ["hi", "hello", "hey", "greetings"]):
                intent.intent = "greeting"
            elif any(word in query for word in ["ping"]):
                intent.intent = "ping"
                # Try to extract IP addresses using basic regex
                ip_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
                ip_matches = re.findall(ip_pattern, original_input)
                intent.entities.ip_addresses = ip_matches

            return intent

    def planner_node(self, state: AgentState):
        """The planner node that creates an execution plan from the user intent.

        This node takes the structured user intent and chat history, then uses
        the Planner agent to generate a plan of tool calls to satisfy the user's request.

        The method handles potential formatting issues in the LLM response by:
        1. Looking for JSON within triple backticks if present
        2. Falling back to searching for a plan array in the response
        3. Returning an empty plan if parsing fails to avoid crashing

        Args:
            state (AgentState): The current state containing input and chat history.

        Returns:
            A dictionary containing the generated plan.
        """
        # Access the structured intent instead of the raw input
        intent = state["structured_intent"]

        # Quick routing checks based on intent - return early for simple queries
        if intent.intent == "greeting":
            return {
                "response": "Hello! I'm your network assistant. How can I help?",
                "plan": [],
            }
        if intent.is_ambiguous:
            return {
                "response": "Could you please specify which device you are referring to?",
                "plan": [],
            }

        # Generate the plan using the LLM
        plan = self._generate_plan(intent, state["chat_history"])

        # Process the plan to substitute interface names, VLAN IDs, and IP addresses where needed
        processed_plan = self._process_plan_with_entity_placeholders(plan, intent)

        return {"plan": processed_plan}

    def _generate_plan(
        self, intent: UserIntent, chat_history: List[BaseMessage]
    ) -> List[dict]:
        """Generate a plan by invoking the planner LLM with the intent and chat history.

        Args:
            intent: The structured intent from NLP preprocessing
            chat_history: The conversation history

        Returns:
            A list of plan steps
        """
        prompt = get_planner_prompt()
        planner_chain = prompt | self.llm
        # Convert to JSON string for the prompt as expected by the template
        input_json = intent.model_dump_json(indent=2)
        response = planner_chain.invoke(
            {"input": input_json, "chat_history": chat_history}
        )

        # Handle the LLM response that may not be valid JSON
        content = response.content.strip()

        # Try to extract JSON from the response content
        # Look for JSON within triple backticks if present
        json_match = re.search(r"```(?:json)?\s*({.*?})\s*```", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content

        try:
            # Attempt to parse the response as JSON
            parsed_response = json.loads(json_str)
            plan = parsed_response.get("plan", [])
        except json.JSONDecodeError:
            # If we can't parse as JSON, try to extract it with more robust pattern matching
            # Look for a JSON array that would represent the plan
            plan_match = re.search(r'"plan"\s*:\s*(\[[^\]]*\])', content, re.DOTALL)
            if plan_match:
                try:
                    # Extract and parse the plan array from the response
                    plan = json.loads(plan_match.group(1))
                except json.JSONDecodeError:
                    # If still unable to parse, return an empty plan to avoid crashing
                    print(f"Could not parse plan from response: {content[:200]}...")
                    plan = []
            else:
                # If no plan found, return an empty plan to avoid crashing
                print(f"No plan found in response: {content[:200]}...")
                plan = []

        return plan

    def _process_plan_with_entity_placeholders(
        self, plan: List[dict], intent: UserIntent
    ) -> List[dict]:
        """Process the plan to substitute interface names, VLAN IDs, and IP addresses where needed.

        Args:
            plan: The original plan from the LLM
            intent: The structured intent containing entity information

        Returns:
            A processed plan with placeholders replaced by actual values
        """
        processed_plan = []
        for step in plan:
            if isinstance(step, dict) and "args" in step and "command" in step["args"]:
                command = step["args"]["command"]
                interfaces = intent.entities.interfaces
                vlans = intent.entities.vlans
                ip_addresses = intent.entities.ip_addresses

                # If the command contains interface_name placeholder and we have interfaces
                if "{interface_name}" in command and interfaces:
                    # Use the first interface from the list
                    command = command.replace("{interface_name}", interfaces[0])
                    step["args"]["command"] = command

                # If the command contains vlan_id placeholder and we have VLANs
                if "{vlan_id}" in command and vlans:
                    # Use the first VLAN from the list
                    command = command.replace("{vlan_id}", vlans[0])
                    step["args"]["command"] = command

                # If the command contains ip_address placeholder and we have IP addresses
                if "{ip_address}" in command and ip_addresses:
                    # Use the first IP address from the list
                    command = command.replace("{ip_address}", ip_addresses[0])
                    step["args"]["command"] = command
            processed_plan.append(step)

        return processed_plan

    def executor_node(self, state: AgentState):
        """The executor node that runs the planned tool calls.

        This node executes the plan created by the planner node by calling the
        tool executor with the planned steps.

        Args:
            state (AgentState): The current state containing the execution plan.

        Returns:
            A dictionary containing the results of tool execution.
        """
        plan = state["plan"]
        print(f"🔍 Executing plan with {len(plan)} steps...")
        results = tool_executor(plan)
        print(f"✅ Plan execution completed with {len(results)} results")
        return {"tool_results": results}

    def generator_node(self, state: AgentState):
        """The generator node that synthesizes the final response.

        This node takes the tool execution results and generates a human-readable
        response to the user's original question.

        Args:
            state (AgentState): The current state containing plan and results.

        Returns:
            A dictionary containing the synthesized response.
        """
        # Construct the context for the LLM with user query, execution plan, and results
        context = f"""
        User's Original Question: {state["input"]}
        Your Plan: {state["plan"]}
        Results of Executing Plan: {[res.model_dump() if hasattr(res, "model_dump") else res for res in state["tool_results"]]}

        Based on the plan and the results, provide a clear, concise, and friendly answer to the user's original question.
        Synthesize all information into a single, coherent response.
        """
        # Invoke the LLM to generate the final response
        response = self.llm.invoke(context)
        return {"response": response.content}

    def run(self, query: str, chat_history: List[BaseMessage]):
        """Runs the workflow with the given query and chat history.

        Executes the full workflow to process a user's query and return a response.

        Args:
            query (str): The raw user query in natural language.
            chat_history (List[BaseMessage]): The conversation history.

        Returns:
            str: The final response to the user's query.
        """
        try:
            # Note: The input needs to be the raw query for the preprocessor node
            inputs = {"input": query, "chat_history": chat_history}
            final_state = self.graph.invoke(inputs)
            return final_state["response"]
        except KeyboardInterrupt:
            # Ensure all network sessions are closed if user interrupts the workflow
            from src.tools.inventory import network_manager

            network_manager.close_all_sessions()
            raise  # Re-raise the KeyboardInterrupt to maintain the expected behavior
