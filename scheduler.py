"""Tweet scheduler — posts at configured intervals during active hours."""

import random
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TweetScheduler:
    """Manages scheduled tweet posting."""

    def __init__(self, poster, content_generator, config, media_manager=None):
        self.poster = poster
        self.content = content_generator
        self.config = config
        self.media = media_manager
        self.posts_today = 0
        self.current_day = None

    def run(self, dry_run=False):
        """Main loop — posts tweets throughout the day."""
        print(f"\n🚀 Buzzr Tweet Bot started!")
        print(f"   Posts per day: {self.config.posts_per_day}")
        print(f"   Active hours: {self.config.active_hours['start']}:00 - {self.config.active_hours['end']}:00")
        print(f"   Dry run: {dry_run}")
        print(f"   Press Ctrl+C to stop.\n")

        while True:
            try:
                now = datetime.now()

                # Reset daily counter
                if self.current_day != now.date():
                    self.current_day = now.date()
                    self.posts_today = 0
                    logger.info(f"New day: {self.current_day}. Resetting post count.")

                # Check if we're in active hours
                if not self._in_active_hours(now):
                    sleep_mins = random.randint(10, 30)
                    logger.info(f"Outside active hours. Sleeping {sleep_mins} min...")
                    time.sleep(sleep_mins * 60)
                    continue

                # Check if we've hit the daily limit
                if self.posts_today >= self.config.posts_per_day:
                    logger.info("Daily post limit reached. Waiting for tomorrow.")
                    time.sleep(3600)
                    continue

                # Generate and post
                tweet = self.content.generate()
                media_path = self.media.pick_media() if self.media else None
                success, result = self.poster.post(tweet, media_path=media_path, dry_run=dry_run)

                if success:
                    self.posts_today += 1
                    logger.info(f"Post {self.posts_today}/{self.config.posts_per_day} for today.")

                # Calculate next post time with jitter
                interval = self._calculate_interval()
                jitter = random.randint(-15, 15) * 60  # +/- 15 min jitter
                sleep_time = max(interval + jitter, 300)  # Minimum 5 min between posts

                logger.info(f"Next post in {sleep_time // 60} minutes.")
                time.sleep(sleep_time)

            except KeyboardInterrupt:
                print("\n\n👋 Bot stopped. See you next time!")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(300)

    def _in_active_hours(self, now):
        """Check if current time is within active posting hours."""
        start = self.config.active_hours.get("start", 9)
        end = self.config.active_hours.get("end", 23)
        return start <= now.hour < end

    def _calculate_interval(self):
        """Calculate seconds between posts to spread them across active hours."""
        start = self.config.active_hours.get("start", 9)
        end = self.config.active_hours.get("end", 23)
        active_seconds = (end - start) * 3600
        remaining_posts = self.config.posts_per_day - self.posts_today

        if remaining_posts <= 0:
            return 3600

        return active_seconds // remaining_posts
