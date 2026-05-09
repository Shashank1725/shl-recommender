from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import List, Optional
import logging

from agent import get_recommendations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational agent for SHL assessment recommendations",
    version="1.0.0"
)

class Message(BaseModel):
    role: str       
    content: str

    @validator("role")
    def role_must_be_valid(cls, v):
        if v not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return v

    @validator("content")
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v.strip()


class ChatRequest(BaseModel):
    messages: List[Message]

    @validator("messages")
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError("messages list cannot be empty")
        if len(v) > 20:
            raise ValueError("Too many messages (max 20)")
        if v[-1].role != "user":
            raise ValueError("Last message must be from user")
        return v


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    logger.info(f"Chat request: {len(messages)} messages")

    try:
        reply, recommendations, end_of_conversation = get_recommendations(messages)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    if not reply:
        reply = "Sorry, there is a problem . Please try again."

    response = ChatResponse(
        reply=reply,
        recommendations=[
            Recommendation(
                name=r["name"],
                url=r["url"],
                test_type=r.get("test_type", "")
            )
            for r in recommendations
        ],
        end_of_conversation=end_of_conversation
    )

    logger.info(f"Response: {len(recommendations)} recommendations, EOC={end_of_conversation}")
    return response
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
