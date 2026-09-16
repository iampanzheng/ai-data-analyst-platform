from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: str


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)
