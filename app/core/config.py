from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    IOT_API_KEY: str
    GRAFANA_API_KEY: str

    # Environment / behavior
    ENV: str = "development"
    RUN_DB_INIT: bool = True
    SQLALCHEMY_ECHO: bool = False

    class Config:
        env_file = ".env"


settings = Settings()