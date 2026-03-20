"""RSS news feed monitor — pulls sports headlines and generates reactive tweets."""

import json
import logging
import time
import hashlib
from datetime import datetime
from pathlib import Path

import feedparser
import requests

logger = logging.getLogger(__name__)

# Sports RSS feeds — free, no auth needed
SPORTS_FEEDS = {
    "espn_top": "https://www.espn.com/espn/rss/news",
    "espn_nba": "https://www.espn.com/espn/rss/nba/news",
    "espn_nfl": "https://www.espn.com/espn/rss/nfl/news",
    "espn_mlb": "https://www.espn.com/espn/rss/mlb/news",
    "espn_soccer": "https://www.espn.com/espn/rss/soccer/news",
    "bleacher_report": "https://bleacherreport.com/articles/feed",
}

SEEN_FILE = Path(__file__).parent / ".seen_articles.json"

# The voice/style for AI-generated tweets
SYSTEM_PROMPT = """You are a witty sports Twitter account promoting Buzzr, a sports rating app (like Letterboxd/Rotten Tomatoes for sports). 

Your style:
- Short, punchy, Gen Z Twitter humor
- Use emojis naturally (not overdone): 😭💀🔥👀🍿
- Always plug Buzzr naturally at the end
- Include @the_real_buzzr handle
- Include the TestFlight link: testflight.apple.com/join/qVRhP4xg
- Keep under 280 characters total
- React to the news like a real fan, not a brand
- Use lowercase casually, no periods at end of sentences
- Reference Buzzr features: rating games 1-10, badges, leaderboard, watch events

Example styles:
- "7'6\" with a pull-up middy is genuinely a cheat code 😭 rate this game live: testflight.apple.com/join/qVRhP4xg @the_real_buzzr"
- "the scouting report just says 'pray' in bold letters 😭😭 rate the madness with us 👇 testflight.apple.com/join/qVRhP4xg @the_real_buzzr"
- "prettiest player to ever touch a basketball. no debate 🎨 rate it on @the_real_buzzr — join: testflight.apple.com/join/qVRhP4xg"

Generate ONE tweet only. No quotes around it. No explanation."""

USER_PROMPT_TEMPLATE = """React to this sports headline and write a tweet that naturally plugs Buzzr:

Headline: {headline}
Summary: {summary}

Write one short, witty tweet (under 280 chars) that reacts to this news and plugs Buzzr."""


class NewsReactor:
    """Monitors sports RSS feeds and generates reactive tweets using AI."""

    def __init__(self, openrouter_api_key=None, model=None):
        self.api_key = openrouter_api_key
        self.model = model or "meta-llama/llama-3.1-8b-instruct:free"
        self._load_seen()

    def _load_seen(self):
        """Load previously seen article IDs."""
        if SEEN_FILE.exists():
            with open(SEEN_FILE) as f:
                self.seen = json.load(f)
        else:
            self.seen = {}

    def _save_seen(self):
        """Save seen article IDs."""
        # Keep only last 500 entries to prevent unbounded growth
        if len(self.seen) > 500:
            sorted_items = sorted(self.seen.items(), key=lambda x: x[1], reverse=True)
            self.seen = dict(sorted_items[:300])
        with open(SEEN_FILE, "w") as f:
            json.dump(self.seen, f, indent=2)

    def _article_id(self, entry):
        """Generate a unique ID for an article."""
        raw = (entry.get("title", "") + entry.get("link", "")).encode()
        return hashlib.md5(raw).hexdigest()

    def fetch_new_headlines(self, max_per_feed=3):
        """Fetch new headlines from all RSS feeds."""
        new_articles = []
        for name, url in SPORTS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:max_per_feed]:
                    aid = self._article_id(entry)
                    if aid not in self.seen:
                        new_articles.append({
                            "id": aid,
                            "source": name,
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", "")[:200],
                            "link": entry.get("link", ""),
                        })
                        self.seen[aid] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Failed to fetch {name}: {e}")
        
        self._save_seen()
        logger.info(f"Found {len(new_articles)} new articles across {len(SPORTS_FEEDS)} feeds.")
        return new_articles

    def generate_reactive_tweet(self, headline, summary):
        """Use OpenRouter (free model) to generate a reactive tweet."""
        if not self.api_key:
            logger.warning("No OpenRouter API key — using template fallback.")
            return self._fallback_tweet(headline)

        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                            headline=headline, summary=summary
                        )},
                    ],
                    "max_tokens": 150,
                    "temperature": 0.9,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            tweet = data["choices"][0]["message"]["content"].strip()
            
            # Clean up: remove surrounding quotes if present
            if tweet.startswith('"') and tweet.endswith('"'):
                tweet = tweet[1:-1]
            
            # Ensure it's under 280 chars
            if len(tweet) > 280:
                tweet = tweet[:277] + "..."
            
            # Ensure the plug is there
            if "testflight" not in tweet.lower() and "buzzr" not in tweet.lower():
                tweet = tweet[:200] + " rate it on @the_real_buzzr 👇 testflight.apple.com/join/qVRhP4xg"
            
            logger.info(f"AI generated tweet ({len(tweet)} chars): {tweet[:80]}...")
            return tweet
        except Exception as e:
            logger.error(f"OpenRouter API failed: {e}")
            return self._fallback_tweet(headline)

    def _fallback_tweet(self, headline):
        """Template-based fallback if AI is unavailable."""
        import random
        templates = [
            f"{headline[:120]} 🔥 rate it on @the_real_buzzr — join: testflight.apple.com/join/qVRhP4xg",
            f"this is why we built Buzzr 😭 {headline[:100]} — rate it 👇 testflight.apple.com/join/qVRhP4xg @the_real_buzzr",
            f"{headline[:120]} 👀 come rate this with us: testflight.apple.com/join/qVRhP4xg @the_real_buzzr",
        ]
        tweet = random.choice(templates)
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
        return tweet

    def get_reactive_tweet(self):
        """Fetch news and generate one reactive tweet. Returns (tweet, article) or (None, None)."""
        articles = self.fetch_new_headlines()
        if not articles:
            logger.info("No new articles to react to.")
            return None, None

        # Pick the first (most recent) new article
        article = articles[0]
        tweet = self.generate_reactive_tweet(article["title"], article["summary"])
        return tweet, article
