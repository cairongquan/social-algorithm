"""项目配置定义。"""

from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """环境变量与应用默认配置。"""
    PROJECT_NAME: str = "Social Algorithm Service"
    PROJECT_DESCRIPTION: str = "Backend service for social algorithm platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    BACKEND_CORS_ORIGINS: List[Union[str, None]] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
