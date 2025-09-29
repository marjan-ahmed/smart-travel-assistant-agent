from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()  # Try current directory first
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))  # Try parent directory

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

try:
    # Load environment variables from root directory
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    from smart_travel_assistant_agent.main import (
        TravelAgent, dynamic_instructions, UserProfile, 
        RunConfig, Runner, InputGuardrailTripwireTriggered, 
        model, ToolLogger
    )
    from openai.types.responses import ResponseTextDeltaEvent
    IMPORT_SUCCESS = True
    print("Successfully imported all modules!")
except Exception as e:
    print(f"Import error: {e}")
    IMPORT_SUCCESS = False

app = FastAPI(title="Smart Travel Assistant API")

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "Smart Travel Assistant API is running!", "imports_ok": IMPORT_SUCCESS}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if not IMPORT_SUCCESS:
        raise HTTPException(status_code=500, detail="Backend modules not properly loaded")
    
    if not req.message.strip():
        return ChatResponse(response="Please ask me something about travel!")
    
    try:
        user_profile = UserProfile(name="Web User", preferences=["vegan", "museums"])
        tool_logger = ToolLogger()
        
        # Run the agent with the user's message
        result = Runner.run_streamed(
            TravelAgent, 
            req.message, 
            context=user_profile, 
            hooks=tool_logger, 
            run_config=RunConfig(model)
        )
        
        response_text = ""
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                response_text += str(event.data.delta)
        
        # If no response was generated, provide a default
        if not response_text.strip():
            response_text = "I'm here to help you with travel planning! Ask me about weather, restaurants, or itineraries for any destination."
            
        return ChatResponse(response=response_text.strip())
        
    except InputGuardrailTripwireTriggered:
        return ChatResponse(response="Sorry, I can't answer that type of question. Please ask me about travel-related topics.")
    except Exception as e:
        print(f"Error processing chat: {e}")
        return ChatResponse(response="I apologize, but I'm having trouble processing your request right now. Please try asking about travel destinations, weather, or restaurants.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)