from langchain_openai import ChatOpenAI
from src.backend.config import settings

def create_openai_llm(model_name: str):
    return ChatOpenAI(
        model=model_name,
        api_key=settings.openai_api_key,
        temperature=0.0,
    )