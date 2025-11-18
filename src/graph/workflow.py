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
        input (UserIntent): The structured input from the NLP pre-processor.
        chat_history (List[BaseMessage]): The conversation history.
        plan (List[dict]): The execution plan created by the planner agent.
        tool_results (List[any]): Results from executing the plan.
        response (str): The final synthesized response to the user.
    """

    input: UserIntent
    chat_history: List[BaseMessage]
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
            groq_api_key=api_key,
            model_name=settings.groq_model_name,
            temperature=settings.groq_temperature
        )
        self.graph = self._build_graph()

    def _build_graph(self):
        """Builds the LangGraph workflow with planner, executor, and generator nodes.

        Creates a state graph with three nodes that process the request in sequence:
        1. Planner node creates an execution plan
        2. Executor node executes the plan
        3. Generator node synthesizes the final response

        Returns:
            The compiled LangGraph workflow.
        """
        workflow = StateGraph(AgentState)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("executor", self.executor_node)
        workflow.add_node("generator", self.generator_node)
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "generator")
        workflow.add_edge("generator", END)
        return workflow.compile()

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
        prompt = get_planner_prompt()
        planner_chain = prompt | self.llm
        # Convert to JSON string for the prompt as expected by the template
        input_json = state["input"].model_dump_json(indent=2)
        response = planner_chain.invoke(
            {"input": input_json, "chat_history": state["chat_history"]}
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

        return {"plan": plan}

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
        print(f"🔍 Executing plan: {plan}")
        results = tool_executor(plan)
        print(f"✅ Plan execution completed, results: {len(results)} items")
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
        User's Original Question: {state["input"].query}
        Your Plan: {state["plan"]}
        Results of Executing Plan: {[res.model_dump() if hasattr(res, "model_dump") else res for res in state["tool_results"]]}

        Based on the plan and the results, provide a clear, concise, and friendly answer to the user's original question.
        Synthesize all information into a single, coherent response.
        """
        # Invoke the LLM to generate the final response
        response = self.llm.invoke(context)
        return {"response": response.content}

    def run(self, intent: UserIntent, chat_history: List[BaseMessage]):
        """Runs the workflow with the given intent and chat history.

        Executes the full workflow to process a user's intent and return a response.

        Args:
            intent (UserIntent): The structured intent from the NLP pre-processor.
            chat_history (List[BaseMessage]): The conversation history.

        Returns:
            str: The final response to the user's query.
        """
        inputs = {"input": intent, "chat_history": chat_history}
        final_state = self.graph.invoke(inputs)
        return final_state["response"]
