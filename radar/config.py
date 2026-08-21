from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_token: str | None = os.getenv("TELEGRAM_TOKEN")
    chat_id: str | None = os.getenv("CHAT_ID")
    gemini_key: str | None = os.getenv("GEMINI_KEY")
    brave_search_api_key: str | None = os.getenv("BRAVE_SEARCH_API_KEY")
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY")
    database_url: str | None = os.getenv("DATABASE_URL")
    http_timeout_seconds: float = float(os.getenv("RADAR_HTTP_TIMEOUT", "20"))
    http_user_agent: str = os.getenv(
        "RADAR_HTTP_USER_AGENT",
        "RadarBot/0.1 (+https://github.com/PedroViana42/Radar)",
    )
    api_host: str = os.getenv("RADAR_API_HOST", "127.0.0.1")
    api_port: int = int(os.getenv("RADAR_API_PORT", "8000"))
    api_cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("RADAR_API_CORS_ORIGINS", "").split(",")
        if origin.strip()
    )

    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL não configurado para operação de banco de dados")
        return self.database_url


settings = Settings()
