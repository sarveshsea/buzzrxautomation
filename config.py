"""Configuration loader for Buzzr X Automation Bot."""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from project root
load_dotenv(Path(__file__).parent / ".env")


class Config:
    """Loads credentials from .env and settings from config.json."""

    def __init__(self):
        # Twitter/X API credentials
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "")
        self.api_key = os.getenv("TWITTER_API_KEY", "")
        self.api_secret = os.getenv("TWITTER_API_SECRET", "")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN", "")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

        # OpenRouter for AI tweet generation
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_model = os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"
        )

        # Load settings from config.json
        config_path = Path(__file__).parent / "config.json"
        if config_path.exists():
            with open(config_path) as f:
                self.settings = json.load(f)
        else:
            self.settings = self._default_settings()

    def _default_settings(self):
        return {
            "posts_per_day": 4,
            "active_hours": {"start": 9, "end": 23},
            "content_mix": {
                "promo": 0.30,
                "features": 0.25,
                "engagement": 0.30,
                "tips": 0.15
            },
            "hashtags": ["#Buzzr", "#SportsApp", "#GameDay", "#SportsTakes"],
            "dry_run": False
        }

    def validate(self):
        """Check that required credentials are set."""
        missing = []
        if not self.api_key:
            missing.append("TWITTER_API_KEY")
        if not self.api_secret:
            missing.append("TWITTER_API_SECRET")
        if not self.access_token:
            missing.append("TWITTER_ACCESS_TOKEN")
        if not self.access_token_secret:
            missing.append("TWITTER_ACCESS_TOKEN_SECRET")

        if missing:
            logger.warning(f"Missing credentials: {', '.join(missing)}")
            logger.warning("Fill these in your .env file to enable posting.")
            return False
        return True

    @property
    def posts_per_day(self):
        return self.settings.get("posts_per_day", 4)

    @property
    def active_hours(self):
        return self.settings.get("active_hours", {"start": 9, "end": 23})

    @property
    def content_mix(self):
        return self.settings.get("content_mix", {})

    @property
    def hashtags(self):
        return self.settings.get("hashtags", [])

    @property
    def media_chance(self):
        return self.settings.get("media_chance", 0.6)

    @property
    def dry_run(self):
        return self.settings.get("dry_run", False)
