"""Media manager — picks random images/GIFs to attach to tweets."""

import os
import random
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent / "assets"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
GIF_EXTENSIONS = {".gif"}
ALL_MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | GIF_EXTENSIONS


class MediaManager:
    """Manages local media assets for tweet attachments."""

    def __init__(self, assets_dir=None, media_chance=0.6):
        self.assets_dir = Path(assets_dir) if assets_dir else ASSETS_DIR
        self.media_chance = media_chance  # probability of attaching media
        self._used_media = set()

    def get_media_files(self):
        """List all media files in the assets directory."""
        if not self.assets_dir.exists():
            return []
        return [
            f for f in self.assets_dir.iterdir()
            if f.suffix.lower() in ALL_MEDIA_EXTENSIONS and f.stat().st_size > 100
        ]

    def pick_media(self):
        """Randomly pick a media file to attach. Returns path or None."""
        if random.random() > self.media_chance:
            return None

        files = self.get_media_files()
        if not files:
            logger.warning("No media files found in assets/")
            return None

        # Avoid repeats until all used
        available = [f for f in files if f.name not in self._used_media]
        if not available:
            self._used_media.clear()
            available = files

        chosen = random.choice(available)
        self._used_media.add(chosen.name)
        logger.info(f"Selected media: {chosen.name}")
        return chosen

    def is_gif(self, path):
        """Check if a file is a GIF."""
        return Path(path).suffix.lower() in GIF_EXTENSIONS
