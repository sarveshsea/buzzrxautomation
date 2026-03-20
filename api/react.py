"""Vercel serverless function — react to sports news with AI tweet."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from news import NewsReactor
from poster import TweetPoster


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            config = Config()
            if not config.validate():
                self._respond(500, {"error": "Missing Twitter API credentials", "success": False})
                return

            reactor = NewsReactor(
                openrouter_api_key=config.openrouter_api_key,
                model=config.openrouter_model,
            )
            poster = TweetPoster(config)
            tweet, article = reactor.get_reactive_tweet()

            if not tweet:
                self._respond(200, {"success": True, "message": "No new headlines"})
                return

            success = poster.post(tweet)
            self._respond(200 if success else 500, {
                "success": success,
                "tweet": tweet,
                "type": "reactive",
                "headline": article["title"] if article else None,
            })
        except Exception as e:
            self._respond(500, {"error": str(e), "success": False})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
