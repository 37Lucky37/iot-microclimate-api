from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    IOT_API_KEY: str
    GRAFANA_API_KEY: str

    # Rate limiting (можна переналаштувати через .env)
    IOT_RATE_LIMIT_MAX_REQUESTS: int = 120
    IOT_RATE_LIMIT_WINDOW_SECONDS: int = 60
    GRAFANA_RATE_LIMIT_MAX_REQUESTS: int = 240
    GRAFANA_RATE_LIMIT_WINDOW_SECONDS: int = 60

    class Config:
        env_file = ".env"


settings = Settings()