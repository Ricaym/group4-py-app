from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    openweather_api_key: str = ""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
