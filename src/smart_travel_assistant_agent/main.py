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

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("BASE_URL")

set_tracing_disabled(True)

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


class irrelevent_question(BaseModel):
    question: str
    irrelevent_word: str
    
guardrail_agent = Agent(
    name="Irrelevent Question Checker",
    instructions="Check if user enters words like hack",
    output_type=irrelevent_question
)

@input_guardrail
async def irrelevent_question_checker(ctx: RunContextWrapper[UserProfile], agent: Agent, input: str | list[TResponseInputItem]):
    result = await Runner.run(guardrail_agent, input, context=ctx.context)
    
    return GuardrailFunctionOutput (
        output_info=result.final_output,
        tripwire_triggered=result.final_output.irrelevent_word
    )

@function_tool
def fetch_weather(location: str) -> str:
    return f"the weather of {location} is {random.randint(-10, 34)}°C"

T = TypeVar('T') # it could be string or list of string Lisst[str]

@function_tool(strict_mode=True, description_override="Ask user about the city and cuisine")
def restaurant_finder(cuisine: str) -> List[T] :
  return [
        {"name": "Green Leaf", "cuisine": "Vegan", "rating": 4.7},
        {"name": "Pizza Roma", "cuisine": "Italian", "rating": 4.5}
    ]
    
BudgetAgent: Agent = Agent(
    name="Budget Assistant",
    instructions="Assist user with budget-specific queries",
    model=model
)


TravelAgent: Agent = Agent(
    name="Smart Travel Assistant",
    instructions="Assist users in planning trips with weather, restaurants, and itineraries.",
    model=model,
    tools=[fetch_weather, restaurant_finder],
    handoffs=[BudgetAgent],
    handoff_description="If the user asks budget-specific queries, handoff to a BudgetAgent",
    input_guardrails=[irrelevent_question_checker]
)

async def main() -> None:
    user_profile = UserProfile(name="Marjan Ahmed", preferences=["vegan", "museums"]) 
    result = Runner.run_streamed(TravelAgent, dynamic_instructions, context=user_profile, hooks=tool_log, run_config=RunConfig(model))
    
    try: 
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)
    except InputGuardrailTripwireTriggered:
        print("Sorry, We can't answer irrelevent questions")


def start():
    asyncio.run(main())
