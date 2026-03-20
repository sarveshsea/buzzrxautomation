"""Twitter/X API poster using Tweepy v2."""

import logging
import time
import tweepy

logger = logging.getLogger(__name__)


class TweetPoster:
    """Handles posting tweets via the X API v2."""

    def __init__(self, config):
        self.config = config
        self.client = None
        self._setup_client()

    def _setup_client(self):
        """Initialize the Tweepy v2 client."""
        try:
            self.client = tweepy.Client(
                bearer_token=self.config.bearer_token,
                consumer_key=self.config.api_key,
                consumer_secret=self.config.api_secret,
                access_token=self.config.access_token,
                access_token_secret=self.config.access_token_secret,
                wait_on_rate_limit=True,
            )
            logger.info("Tweepy client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Tweepy client: {e}")
            self.client = None

    def post(self, text, dry_run=False):
        """Post a tweet. Returns True on success."""
        if dry_run:
            logger.info(f"[DRY RUN] Would post: {text}")
            print(f"\n🔸 [DRY RUN] Would post:\n{text}\n")
            return True

        if not self.client:
            logger.error("No Twitter client available. Check your credentials.")
            return False

        try:
            response = self.client.create_tweet(text=text)
            tweet_id = response.data["id"]
            logger.info(f"Tweet posted successfully! ID: {tweet_id}")
            print(f"\n✅ Tweet posted! ID: {tweet_id}")
            print(f"   View: https://x.com/i/status/{tweet_id}\n")
            return True
        except tweepy.TooManyRequests:
            logger.warning("Rate limit hit. Waiting 15 minutes...")
            time.sleep(900)
            return self.post(text, dry_run=dry_run)
        except tweepy.Forbidden as e:
            logger.error(f"Forbidden — check your API access level: {e}")
            return False
        except tweepy.Unauthorized as e:
            logger.error(f"Unauthorized — check your credentials: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            return False

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
