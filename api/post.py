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
        try:
            config = Config()
            if not config.validate():
                self._respond(500, {"error": "Missing Twitter API credentials", "success": False})
                return

            content = ContentGenerator(content_mix=config.content_mix, hashtags=config.hashtags)
            poster = TweetPoster(config)
            tweet = content.generate()
            success = poster.post(tweet)

            self._respond(200 if success else 500, {
                "success": success,
                "tweet": tweet,
                "type": "scheduled",
            })
        except Exception as e:
            self._respond(500, {"error": str(e), "success": False})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
