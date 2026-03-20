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
        config = Config()
        if not config.validate():
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing Twitter API credentials"}).encode())
            return

        reactor = NewsReactor(
            openrouter_api_key=config.openrouter_api_key,
            model=config.openrouter_model,
        )
        poster = TweetPoster(config)
        tweet, article = reactor.get_reactive_tweet()

        if not tweet:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "No new headlines"}).encode())
            return

        success = poster.post(tweet)
        self.send_response(200 if success else 500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": success,
            "tweet": tweet,
            "type": "reactive",
            "headline": article["title"] if article else None,
        }).encode())
