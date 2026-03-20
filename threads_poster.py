"""Threads API poster — cross-posts tweets to Meta Threads."""

import logging
import os
import requests

logger = logging.getLogger(__name__)

THREADS_USER_ID = os.getenv("THREADS_USER_ID", "")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "")
THREADS_API = "https://graph.threads.net/v1.0"


class ThreadsPoster:
    """Posts to Threads via Meta's API. Two-step: create container → publish."""

    def __init__(self):
        self.user_id = THREADS_USER_ID
        self.access_token = THREADS_ACCESS_TOKEN
        self.enabled = bool(self.user_id and self.access_token)
        if self.enabled:
            logger.info("Threads poster initialized.")
        else:
            logger.info("Threads posting disabled (no credentials).")

    def post(self, text, dry_run=False):
        """Post text to Threads. Returns (success, thread_id_or_error)."""
        if not self.enabled:
            return False, "Threads credentials not configured"

        # Threads has 500 char limit
        if len(text) > 500:
            text = text[:497] + "..."

        if dry_run:
            logger.info(f"[DRY RUN] Would post to Threads: {text[:80]}...")
            return True, "dry_run"

        try:
            # Step 1: Create media container
            resp = requests.post(
                f"{THREADS_API}/{self.user_id}/threads",
                params={
                    "media_type": "TEXT",
                    "text": text,
                    "access_token": self.access_token,
                },
                timeout=30,
            )
            resp.raise_for_status()
            creation_id = resp.json().get("id")
            if not creation_id:
                return False, "No creation_id returned from Threads API"

            # Step 2: Publish
            resp2 = requests.post(
                f"{THREADS_API}/{self.user_id}/threads_publish",
                params={
                    "creation_id": creation_id,
                    "access_token": self.access_token,
                },
                timeout=30,
            )
            resp2.raise_for_status()
            thread_id = resp2.json().get("id")
            logger.info(f"Posted to Threads! ID: {thread_id}")
            return True, thread_id

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_detail = e.response.json().get("error", {}).get("message", str(e))
            except Exception:
                error_detail = str(e)
            logger.error(f"Threads API error: {error_detail}")
            return False, f"Threads: {error_detail}"
        except Exception as e:
            logger.error(f"Threads post failed: {e}")
            return False, str(e)
