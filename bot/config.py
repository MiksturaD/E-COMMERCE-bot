from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    bot_token: str = Field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    admin_ids: List[int] = Field(default_factory=lambda: [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()])
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./shop.db"))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

settings = Settings() 