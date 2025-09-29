import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner, RunHooks, InputGuardrailTripwireTriggered, GuardrailFunctionOutput,TResponseInputItem, RunContextWrapper, input_guardrail, function_tool, RunConfig, OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
import random
from typing import TypeVar, List
from pydantic import BaseModel
from dataclasses import dataclass

# Load .env from root directory
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

# Also try to load from backend directory
backend_env = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(backend_env)

GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("BASE_URL")

print(f"Environment loaded - API Key starts with: {GEMINI_API_KEY[:10] if GEMINI_API_KEY else 'None'}...")
print(f"Model: {GEMINI_MODEL}")
print(f"Base URL: {BASE_URL}")

# Check for conflicting environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    print(f"WARNING: OPENAI_API_KEY is set: {openai_api_key[:10]}...")
    # Clear it to avoid conflicts
    os.environ.pop("OPENAI_API_KEY", None)

set_tracing_disabled(True)

# Ensure we're using the Gemini API key explicitly
client = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url=BASE_URL)
model= OpenAIChatCompletionsModel(GEMINI_MODEL, client)

# ----------------------------------------------------------------------------------------------

@dataclass
class UserProfile():
    name: str
    preferences: List[str]

def dynamic_instructions(
    context: RunContextWrapper[UserProfile], agent: Agent[UserProfile]
) -> str:
    return (
        f"The user's name is {context.context.name}. "
        f"They prefer {context.context.preferences}. Tailor restaurant and itinerary suggestions accordingly."
    )
    
class ToolLogger(RunHooks):
    async def on_agent_start(self, context: RunContextWrapper[UserProfile], agent: Agent):
        print(f"[AGENT START] {agent.name} for user {context.context.name}")

    async def on_tool_start(self, context: RunContextWrapper[UserProfile], agent: Agent, tool_ctx):
        print(f"[TOOL START] {tool_ctx.tool.name} called with args {tool_ctx.args}")

    async def on_tool_end(self, context: RunContextWrapper[UserProfile], agent: Agent, tool_ctx, result):
        print(f"[TOOL END] {tool_ctx.tool.name} returned {result}")


@input_guardrail
async def irrelevent_question_checker(ctx: RunContextWrapper[UserProfile], agent: Agent, input: str | list[TResponseInputItem]):
    # Simple keyword-based check for inappropriate content
    if isinstance(input, str):
        blocked_words = ["hack", "exploit", "virus", "malware"]
        if any(word in input.lower() for word in blocked_words):
            return GuardrailFunctionOutput(
                output_info="Blocked inappropriate content",
                tripwire_triggered=True
            )
    
    return GuardrailFunctionOutput(
        output_info="Content is appropriate",
        tripwire_triggered=False
    )

# Temporarily removed function tools to avoid compatibility issues
# We'll re-add them later using a different approach
    
BudgetAgent: Agent = Agent(
    name="Budget Assistant",
    instructions="Assist user with budget-specific queries",
    model=model
)


TravelAgent: Agent = Agent(
    name="Smart Travel Assistant",
    instructions="""You are a helpful travel assistant. Help users with:
    - Travel planning and itineraries
    - Weather information (provide general guidance)
    - Restaurant recommendations (suggest popular options)
    - Transportation advice
    - Local attractions and activities
    
    Be friendly, informative, and helpful. If asked about weather, provide general seasonal information.
    For restaurants, suggest popular cuisines and dining areas in the mentioned city.""",
    model=model,
    handoffs=[BudgetAgent],
    handoff_description="If the user asks budget-specific queries, handoff to a BudgetAgent",
    input_guardrails=[irrelevent_question_checker]
)

async def main() -> None:
    user_profile = UserProfile(name="Marjan Ahmed", preferences=["vegan", "museums"]) 
    tool_logger = ToolLogger()
    result = Runner.run_streamed(TravelAgent, dynamic_instructions, context=user_profile, hooks=tool_logger, run_config=RunConfig(model))
    
    try: 
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
    except InputGuardrailTripwireTriggered:
        print("Sorry, We can't answer irrelevent questions")


def start():
    asyncio.run(main())
