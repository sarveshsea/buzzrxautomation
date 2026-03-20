"""Vercel serverless function — instant AI + RSS tweet post."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from content import ContentGenerator
from news import NewsReactor
from poster import TweetPoster

try:
    from supabase_client import log_post
except Exception:
    log_post = None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            config = Config()
            if not config.validate():
                self._respond(500, {"error": "Missing Twitter API credentials", "success": False})
                return

            poster = TweetPoster(config)
            reactor = NewsReactor(
                openrouter_api_key=config.openrouter_api_key,
                model=config.openrouter_model,
            )

            # Try RSS + AI first
            tweet, article = reactor.get_reactive_tweet()
            source = "cron_vercel"

            # Fallback to template if no news or no AI key
            if not tweet:
                content = ContentGenerator(content_mix=config.content_mix, hashtags=config.hashtags)
                tweet = content.generate()
                article = None
                source = "cron_vercel"

            success, result = poster.post(tweet)

            if success and log_post:
                log_post(
                    tweet=tweet,
                    headline=article["title"] if article else None,
                    source=source,
                    tweet_id=result,
                )

            self._respond(200 if success else 500, {
                "success": success,
                "tweet": tweet,
                "source": source,
                "headline": article["title"] if article else None,
                "error": None if success else result,
                "tweet_id": result if success else None,
            })
        except Exception as e:
            self._respond(500, {"error": str(e), "success": False})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
