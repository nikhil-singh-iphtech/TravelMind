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

    # LLM Settings
    llm_provider: str = "groq"
    llm_api_key: str = ""
    llm_model: str = ""
    groq_api_key: str = ""
    groq_model: str = ""
    gemini_api_key: str = ""

    # Database
    database_url: str = ""
    redis_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    embedding_model: str = "all-MiniLM-L6-v2"

    use_real_weather: bool = False
    duffel_api_key: str = ""
    makcorps_api_key: str = ""
    makcorps_rapidapi_key: str = ""
    use_real_flights: bool = False
    use_real_hotels: bool = False


# Created once, imported everywhere else that needs settings.
settings = Settings()

