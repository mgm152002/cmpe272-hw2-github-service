# Team member: Manoj Ganjigatte Manjunatha (@mgm152002)

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    github_token: str = Field(default="", validation_alias="GITHUB_TOKEN")
    github_owner: str = Field(default="", validation_alias="GITHUB_OWNER")
    github_repo: str = Field(default="", validation_alias="GITHUB_REPO")
    webhook_secret: str = Field(default="", validation_alias="WEBHOOK_SECRET")
    port: int = Field(default=8000, validation_alias="PORT")
    database_path: str = Field(default="data/events.db", validation_alias="DATABASE_PATH")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
