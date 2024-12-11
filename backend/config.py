from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    root_path: str = ""
    logging_level: str = "INFO"
    testing: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
