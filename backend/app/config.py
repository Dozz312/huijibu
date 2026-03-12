from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./huijibu.db"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30
    RESET_HOUR: int = 4
    ADMIN_KEY: str = "hjb-admin-change-me"

    model_config = {"env_file": ".env"}


settings = Settings()
