import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError

load_dotenv() 

class Settings(BaseModel):
    # ======================
    # APP
    # ======================
    env: str = Field(default="development")
    debug: bool = Field(default=False)

    # ======================
    # POSTGRES
    # ======================
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # Optional full URL override
    database_url: str | None = None

    # ======================
    # REDIS
    # ======================
    redis_app_host: str 
    redis_app_port: int = 6379
    redis_app_db: int = 0

    # ======================
    # REDIS (LANGGRAPH)
    # ======================
    redis_checkpointer_host: str 
    redis_checkpointer_port: int = 6380
    redis_checkpointer_db: int = 0

    # ======================
    # AUTH / JWT
    # ======================
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 24

    # ======================
    # LLM
    # ======================
    openai_api_key: str | None = None
    openai_default_model: str = "gpt-5.2"
    openai_mini_model: str = "gpt-5-mini"

def load_settings() -> Settings:
    try:
        return Settings(
            env=os.getenv("ENV", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",

            postgres_host=os.getenv("POSTGRES_HOST"),
            postgres_port=int(os.getenv("POSTGRES_PORT", 5432)),
            postgres_db=os.getenv("POSTGRES_DB"),
            postgres_user=os.getenv("POSTGRES_USER"),
            postgres_password=os.getenv("POSTGRES_PASSWORD"),
            database_url=os.getenv("DATABASE_URL"),

            redis_app_host=os.getenv("REDIS_APP_HOST", "localhost"),
            redis_app_port=int(os.getenv("REDIS_APP_PORT", 6379)),
            redis_app_db=int(os.getenv("REDIS_APP_DB", 0)),

            redis_checkpointer_host=os.getenv("REDIS_CHECKPOINTER_HOST", "localhost"),
            redis_checkpointer_port=int(os.getenv("REDIS_CHECKPOINTER_PORT", 6380)),
            redis_checkpointer_db=0, 

            jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_exp_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 1440)),

            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_default_model=os.getenv("OPENAI_DEFAULT_MODEL"),
            openai_mini_model=os.getenv("OPENAI_MINI_MODEL")
        )
    except ValidationError as e:
        raise RuntimeError(f"❌ Invalid environment configuration:\n{e}")

settings = load_settings()
