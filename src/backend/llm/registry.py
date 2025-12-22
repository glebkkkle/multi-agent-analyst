from src.backend.llm.factory import create_openai_llm
from src.backend.config import settings

_llm_cache = {}

def get_llm(name: str):
    if name not in _llm_cache:
        _llm_cache[name] = create_openai_llm(name)
    return _llm_cache[name]

def get_default_llm():
    return get_llm(settings.openai_default_model)

def get_mini_llm():
    return get_llm(settings.openai_mini_model)
