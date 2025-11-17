"""The core LangGraph workflow for the multi-agent system."""
import json
import re
from typing import List, TypedDict
from langchain_core.messages import BaseMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from src.agents.planner import get_planner_prompt
from src.agents.executor import tool_executor
from src.core.models import UserIntent

class AgentState(TypedDict):
    """Defines the state of the graph."""
    input: UserIntent
    chat_history: List[BaseMessage]
    plan: List[dict]
    tool_results: List[any]
    response: str

class NetworkWorkflow:
    def __init__(self, api_key: str):
        self.llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.1-8b-instant", temperature=0.0)
        self.graph = self._build_graph()

    def _build_graph(self):
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
        prompt = get_planner_prompt()
        planner_chain = prompt | self.llm
        # Convert to JSON string for the prompt as expected by the template
        input_json = state["input"].model_dump_json(indent=2)
        response = planner_chain.invoke({
            "input": input_json,
            "chat_history": state["chat_history"]
        })

        # Handle the LLM response that may not be valid JSON
        content = response.content.strip()

        # Try to extract JSON from the response content
        # Look for JSON within triple backticks if present
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = content

        try:
            parsed_response = json.loads(json_str)
            plan = parsed_response.get("plan", [])
        except json.JSONDecodeError:
            # If we can't parse as JSON, return an empty plan to avoid crashing
            plan = []

        return {"plan": plan}

    def executor_node(self, state: AgentState):
        plan = state["plan"]
        results = tool_executor(plan)
        return {"tool_results": results}

    def generator_node(self, state: AgentState):
        context = f"""
        User's Original Question: {state['input'].query}
        Your Plan: {state['plan']}
        Results of Executing Plan: {[res.model_dump() if hasattr(res, 'model_dump') else res for res in state['tool_results']]}

        Based on the plan and the results, provide a clear, concise, and friendly answer to the user's original question.
        Synthesize all information into a single, coherent response.
        """
        response = self.llm.invoke(context)
        return {"response": response.content}

    def run(self, intent: UserIntent, chat_history: List[BaseMessage]):
        inputs = {"input": intent, "chat_history": chat_history}
        final_state = self.graph.invoke(inputs)
        return final_state["response"]