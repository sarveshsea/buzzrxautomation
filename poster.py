"""Twitter/X API poster using Tweepy v2 with media support + Threads cross-post."""

import logging
import time
import tweepy

try:
    from threads_poster import ThreadsPoster
except Exception:
    ThreadsPoster = None

logger = logging.getLogger(__name__)


class TweetPoster:
    """Handles posting tweets via the X API v2 with optional media."""

    def __init__(self, config):
        self.config = config
        self.client = None
        self.api_v1 = None
        self.threads = ThreadsPoster() if ThreadsPoster else None
        self._setup_client()

    def _setup_client(self):
        """Initialize both Tweepy v2 client and v1.1 API for media uploads."""
        try:
            self.client = tweepy.Client(
                bearer_token=self.config.bearer_token,
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_token_secret,
                wait_on_rate_limit=True,
            )
            # v1.1 API needed for media uploads
            if self.config.api_key and self.config.access_token:
                auth = tweepy.OAuth1UserHandler(
                    self.config.api_key,
                    self.config.api_secret,
                    self.config.access_token,
                    self.config.access_token_secret,
                )
                self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            logger.info("Tweepy client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Tweepy client: {e}")
            self.client = None

    def _upload_media(self, media_path):
        """Upload media file via v1.1 API. Returns media_id or None."""
        if not self.api_v1:
            logger.warning("No v1.1 API client — skipping media upload.")
            return None

        try:
            media = self.api_v1.media_upload(filename=str(media_path))
            logger.info(f"Media uploaded: {media_path.name} -> ID {media.media_id}")
            return media.media_id
        except Exception as e:
            logger.error(f"Media upload failed for {media_path}: {e}")
            return None

    def post(self, text, media_path=None, dry_run=False):
        """Post a tweet with optional media. Returns (success, result_or_error)."""
        if dry_run:
            media_note = f" + media: {media_path.name}" if media_path else ""
            logger.info(f"[DRY RUN] Would post: {text}{media_note}")
            return True, "dry_run"

        if not self.client:
            logger.error("No Twitter client available. Check your credentials.")
            return False, "No Twitter client — credentials missing or invalid"

        try:
            media_ids = None
            if media_path:
                media_id = self._upload_media(media_path)
                if media_id:
                    media_ids = [media_id]

            response = self.client.create_tweet(text=text, media_ids=media_ids)
            tweet_id = response.data["id"]
            logger.info(f"Tweet posted successfully! ID: {tweet_id}")

            # Cross-post to Threads
            if self.threads and self.threads.enabled:
                t_ok, t_result = self.threads.post(text, dry_run=dry_run)
                if t_ok:
                    logger.info(f"Cross-posted to Threads: {t_result}")
                else:
                    logger.warning(f"Threads cross-post failed: {t_result}")

            return True, tweet_id
        except tweepy.TooManyRequests:
            logger.warning("Rate limit hit.")
            return False, "Rate limit hit — try again in 15 minutes"
        except tweepy.Forbidden as e:
            logger.error(f"Forbidden — check your API access level: {e}")
            return False, f"Forbidden: {e}"
        except tweepy.Unauthorized as e:
            logger.error(f"Unauthorized — check your credentials: {e}")
            return False, f"Unauthorized: {e}"
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False, str(e)

    def test_auth(self):
        """Test authentication by fetching the authenticated user."""
        if not self.client:
            print("❌ No client — credentials missing or invalid.")
            return False

        try:
            user = self.client.get_me()
            if user and user.data:
                print(f"✅ Authenticated as: @{user.data.username} ({user.data.name})")
                print(f"   User ID: {user.data.id}")
                return True
            else:
                print("❌ Authentication failed — no user data returned.")
                return False
        except tweepy.Unauthorized:
            print("❌ Unauthorized — your API keys or tokens are invalid.")
            print("   Regenerate them at https://developer.x.com/en/portal/dashboard")
            return False
        except Exception as e:
            print(f"❌ Auth test failed: {e}")
            return False
