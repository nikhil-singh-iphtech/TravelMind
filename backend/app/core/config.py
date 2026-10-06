from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application configuration.

    Values are loaded from environment variables, falling back to
    a local .env file if present. Pydantic validates types for us
    (e.g. if LOG_LEVEL were an int field and someone set it to
    "banana", this would fail fast at startup instead of later).
    """

    app_name: str = "TravelMind"
    environment: str = "development"
    log_level: str = "INFO"

    # Placeholders for future phases — safe to leave blank for now
    database_url: str = ""
    redis_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""

    groq_api_key: str = ""
    groq_model: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    embedding_model: str = "all-MiniLM-L6-v2"

    use_real_weather: bool = False


# Created once, imported everywhere else that needs settings.
settings = Settings()
