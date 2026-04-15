from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "wechat-knowledge-agent"
    environment: str = "dev"

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_vector_store_id: str = Field(default="", alias="OPENAI_VECTOR_STORE_ID")

    gewechat_api_base: str = Field(default="", alias="GEWECHAT_API_BASE")
    gewechat_token: str = Field(default="", alias="GEWECHAT_TOKEN")
    gewechat_webhook_secret: str = Field(default="", alias="GEWECHAT_WEBHOOK_SECRET")

    allowed_contacts: str = Field(default="", alias="ALLOWED_CONTACTS")
    confidence_threshold: float = Field(default=0.55, alias="CONFIDENCE_THRESHOLD")

    interaction_log_path: Path = Field(default=Path("logs/interactions.jsonl"), alias="INTERACTION_LOG_PATH")

    @property
    def allowed_contact_set(self) -> set[str]:
        if not self.allowed_contacts.strip():
            return set()
        return {i.strip() for i in self.allowed_contacts.split(",") if i.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
