from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    data_dir: Path = Path("/data")
    puzzles_dir: Path = Path("/app/puzzles")
    static_dir: Path = Path("/app/static")
    discord_client_id: str
    discord_client_secret: str
    public_origin: str  # e.g. https://lol.example.com, no trailing slash
    session_days: int = 30
    chrono_grace_s: float = 2.0
    timezone: str = "Europe/Paris"

    @property
    def discord_redirect_uri(self) -> str:
        return f"{self.public_origin}/api/auth/callback"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def ddragon_dir(self) -> Path:
        return self.data_dir / "ddragon"


@lru_cache
def get_settings() -> Settings:
    return Settings()
