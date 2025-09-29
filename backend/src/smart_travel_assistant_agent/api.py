from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from smart_travel_assistant_agent.main import TravelAgent, dynamic_instructions, UserProfile, RunConfig, Runner, InputGuardrailTripwireTriggered, model, ToolLogger
from openai.types.responses import ResponseTextDeltaEvent

app = FastAPI()

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    user_profile = UserProfile(name="Web User", preferences=["vegan", "museums"])
    tool_logger = ToolLogger()
    result = Runner.run_streamed(TravelAgent, req.message, context=user_profile, hooks=tool_logger, run_config=RunConfig(model))
    response_text = ""
    try:
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                response_text += str(event.data.delta)
    except InputGuardrailTripwireTriggered:
        response_text = "Sorry, we can't answer irrelevent questions."
    return {"response": response_text.strip() if response_text.strip() else "I'm here to help you with travel planning! Ask me about weather, restaurants, or itineraries."}
