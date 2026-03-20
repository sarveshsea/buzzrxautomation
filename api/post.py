"""Vercel serverless function — post a scheduled tweet."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from content import ContentGenerator
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

        content = ContentGenerator(content_mix=config.content_mix, hashtags=config.hashtags)
        poster = TweetPoster(config)
        tweet = content.generate()
        success = poster.post(tweet)

        self.send_response(200 if success else 500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": success,
            "tweet": tweet,
            "type": "scheduled",
        }).encode())
