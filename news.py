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
    "espn_nhl": "https://www.espn.com/espn/rss/nhl/news",
    "espn_soccer": "https://www.espn.com/espn/rss/soccer/news",
    "espn_mma": "https://www.espn.com/espn/rss/mma/news",
    "espn_ncaab": "https://www.espn.com/espn/rss/ncb/news",
    "espn_ncaaf": "https://www.espn.com/espn/rss/ncf/news",
    "bleacher_report": "https://bleacherreport.com/articles/feed",
    "cbssports": "https://www.cbssports.com/rss/headlines/",
    "yahoo_sports": "https://sports.yahoo.com/rss/",
}

# Use /tmp for serverless (Vercel), fallback to project dir locally
try:
    SEEN_FILE = Path("/tmp/.seen_articles.json")
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
except Exception:
    SEEN_FILE = Path(__file__).parent / ".seen_articles.json"

# The voice/style for AI-generated tweets
SYSTEM_PROMPT = """You are a witty sports Twitter account promoting Buzzr, a sports rating app (like Letterboxd/Rotten Tomatoes for sports).

ENGAGEMENT RULES (critical for algorithm):
- Keep under 200 characters (shorter tweets get 2x more engagement)
- Start with a HOOK — first 5 words must grab attention (hot take, question, bold claim)
- Use max 1 hashtag, only if natural. No hashtag walls
- End with a question or CTA to drive replies (replies = algorithm boost)
- React like a real fan, not a brand — lowercase, no periods, casual

Your voice:
- Short, punchy, Gen Z Twitter humor — the kind that gets screenshotted and shared
- Use emojis naturally but sparingly (1-3 max): 😭💀🔥👀🍿🧱🎨👨‍🍳🏆
- Plug Buzzr naturally at the end — never forced
- Include @the_real_buzzr handle
- Use sports slang: cooking, bucket, dawg, hooper, box office, cheat code

HOOK FORMATS THAT WORK:
- Hot take opener: "unpopular opinion:" / "i'm sorry but" / "no one's saying it so i will"
- Question hook: "how are we not talking about" / "am i crazy or"
- Bold claim: "this might be the best ___" / "there's no way ___"
- Fan reaction: "bro just ___" / "he really just ___"

Example tweets (match THIS energy):
- "imagine thinking you have a lane to the rim and you see 7'4 of THIS waiting 🧱 rate it @the_real_buzzr"
- "the scouting report just says 'pray' in bold letters 😭 how you rating this? @the_real_buzzr"
- "he's not cooking he's catering the entire arena 🍽️ what's the rating? @the_real_buzzr"
- "am i crazy or is this the best game of the year 🔥 rate it on @the_real_buzzr"
- "no one's saying it so i will — this man is the MVP 👀 agree? @the_real_buzzr"
- "bro just dropped 40 like it was nothing 💀 how you rating this @the_real_buzzr"

Generate ONE tweet only. No quotes. No explanation. Under 200 characters."""

USER_PROMPT_TEMPLATE = """React to this sports headline and write a tweet that naturally plugs Buzzr:

Headline: {headline}
Summary: {summary}

Write one short, witty tweet (under 280 chars) that reacts to this news and plugs Buzzr."""


class NewsReactor:
    """Monitors sports RSS feeds and generates reactive tweets using AI."""

    def __init__(self, openrouter_api_key=None, model=None):
        self.api_key = openrouter_api_key
        self.model = model or "arcee-ai/arcee-blitz:free"
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

    def fetch_headlines(self, max_per_feed=5):
        """Fetch latest headlines from all RSS feeds (display only, doesn't mark as seen)."""
        articles = []
        for name, url in SPORTS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:max_per_feed]:
                    # Extract image from media_content, media_thumbnail, or enclosures
                    image = ""
                    if hasattr(entry, "media_content") and entry.media_content:
                        image = entry.media_content[0].get("url", "")
                    elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                        image = entry.media_thumbnail[0].get("url", "")
                    elif hasattr(entry, "enclosures") and entry.enclosures:
                        for enc in entry.enclosures:
                            if enc.get("type", "").startswith("image"):
                                image = enc.get("href", enc.get("url", ""))
                                break
                    articles.append({
                        "id": self._article_id(entry),
                        "source": name,
                        "title": entry.get("title", ""),
                        "summary": entry.get("summary", "")[:200],
                        "link": entry.get("link", ""),
                        "image": image,
                    })
            except Exception as e:
                logger.error(f"Failed to fetch {name}: {e}")
        logger.info(f"Fetched {len(articles)} headlines across {len(SPORTS_FEEDS)} feeds.")
        return articles

    def fetch_new_headlines(self, max_per_feed=3):
        """Fetch new headlines and mark them as seen (for posting)."""
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
