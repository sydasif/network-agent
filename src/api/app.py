"""FastAPI application for the AI Network Agent.

This module provides REST API endpoints for the network agent, allowing users to
interact with the system programmatically. The API exposes endpoints for intent
processing, planning, execution, and full workflow operations.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from src.graph.workflow import NetworkWorkflow
from src.core.config import settings
from src.tools.inventory import network_manager
from langchain_core.messages import AIMessage, HumanMessage


class UserQuery(BaseModel):
    """Request model for user queries to the network agent."""
    text: str
    chat_history: Optional[List[Dict[str, str]]] = []


class IntentResponse(BaseModel):
    """Response model for intent processing."""
    query: str
    intent: str
    entities: Dict[str, Any]
    sentiment: str
    is_ambiguous: bool


class PlanResponse(BaseModel):
    """Response model for planning."""
    plan: List[Dict[str, Any]]
    reasoning: str


class ExecutionResponse(BaseModel):
    """Response model for execution results."""
    results: List[Any]


class WorkflowResponse(BaseModel):
    """Response model for full workflow execution."""
    response: str
    intent: Optional[IntentResponse] = None
    plan: Optional[List[Dict[str, Any]]] = None
    results: Optional[List[Any]] = None


def _convert_chat_history(chat_history_data: Optional[List[Dict[str, str]]]) -> List:
    """Convert chat history from API format to LangChain format."""
    chat_history = []
    if chat_history_data:
        for msg in chat_history_data:
            if msg.get("role") == "user":
                chat_history.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                chat_history.append(AIMessage(content=msg.get("content", "")))
    return chat_history


def _get_structured_intent(text: str):
    """Extract structured intent from text using the workflow's intent classifier."""
    if not workflow:
        raise HTTPException(status_code=500, detail="Workflow not initialized")

    intent_classifier = workflow.intent_classifier
    return intent_classifier.invoke(text)


# Create FastAPI app instance
app = FastAPI(
    title="AI Network Agent API",
    description="REST API for the AI Network Agent that provides NLP-driven network management capabilities",
    version="1.0.0"
)


# Initialize components once at startup
workflow = None


@app.on_event("startup")
def startup_event():
    """Initialize the NLP processor and workflow on application startup."""
    global workflow

    groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not set! Please set the environment variable.")

    if not os.path.exists(settings.inventory_file):
        raise FileNotFoundError(f"Inventory file '{settings.inventory_file}' not found.")

    try:
        workflow = NetworkWorkflow(api_key=groq_api_key)
        print("✅ API components initialized successfully.")
    except Exception as e:
        print(f"❌ Error during API initialization: {e}")
        raise


@app.get("/")
def read_root():
    """Root endpoint for API health check."""
    return {"message": "AI Network Agent API is running!", "status": "healthy"}


@app.post("/intent", response_model=IntentResponse)
def extract_intent(query: UserQuery):
    """Extract intent and entities from a user's natural language query.

    Args:
        query (UserQuery): The user's query text

    Returns:
        IntentResponse: Structured representation of intent and extracted entities
    """
    try:
        structured_intent = _get_structured_intent(query.text)

        return IntentResponse(
            query=query.text,
            intent=structured_intent.intent,
            entities=structured_intent.entities.model_dump(exclude_none=True),
            sentiment=structured_intent.sentiment,
            is_ambiguous=structured_intent.is_ambiguous
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing intent: {str(e)}")


@app.post("/plan", response_model=PlanResponse)
def create_plan(query: UserQuery):
    """Create an execution plan for a user's query.

    Args:
        query (UserQuery): The user's query text

    Returns:
        PlanResponse: Execution plan containing tool calls
    """
    try:
        if not workflow:
            raise HTTPException(status_code=500, detail="Components not initialized")

        structured_intent = _get_structured_intent(query.text)
        chat_history = _convert_chat_history(query.chat_history)

        # Create state for the planner node
        from src.graph.workflow import AgentState
        state: AgentState = {
            "structured_intent": structured_intent,
            "input": query.text,
            "chat_history": chat_history,
            "plan": [],
            "tool_results": [],
            "response": ""
        }

        # Call the planner node
        plan_result = workflow.planner_node(state)
        plan = plan_result.get("plan", [])

        return PlanResponse(
            plan=plan,
            reasoning="Plan generated from intent and context"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating plan: {str(e)}")


@app.post("/execute", response_model=ExecutionResponse)
def execute_plan(steps: List[Dict[str, Any]]):
    """Execute a previously created plan.

    Args:
        steps (List[Dict[str, Any]]): The plan steps to execute

    Returns:
        ExecutionResponse: Results of the plan execution
    """
    try:
        from src.agents.executor import tool_executor

        results = tool_executor(steps)

        return ExecutionResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing plan: {str(e)}")


@app.post("/workflow", response_model=WorkflowResponse)
def run_workflow(query: UserQuery):
    """Run the complete workflow from intent to response.

    This endpoint processes a user query through the complete pipeline:
    NLP processing → Planning → Execution → Response generation

    Args:
        query (UserQuery): The user's query text

    Returns:
        WorkflowResponse: Complete response with optional intermediate results
    """
    try:
        if not workflow:
            raise HTTPException(status_code=500, detail="Components not initialized")

        chat_history = _convert_chat_history(query.chat_history)

        # Process the query through the entire workflow
        response = workflow.run(query.text, chat_history)

        # Get the intent for the response (this would need to be extracted from the workflow execution)
        structured_intent = _get_structured_intent(query.text)

        return WorkflowResponse(
            response=response,
            intent=IntentResponse(
                query=query.text,
                intent=structured_intent.intent,
                entities=structured_intent.entities.model_dump(exclude_none=True),
                sentiment=structured_intent.sentiment,
                is_ambiguous=structured_intent.is_ambiguous
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running workflow: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint to verify API status."""
    try:
        # Check if we can access the inventory
        device_count = len(network_manager.devices)
        return {
            "status": "healthy",
            "devices_connected": device_count,
            "nlp_processor_ready": True,  # For backward compatibility
            "workflow_ready": workflow is not None
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.on_event("shutdown")
def shutdown_event():
    """Close all network sessions on application shutdown."""
    print("Shutting down... closing all network sessions.")
    network_manager.close_all_sessions()