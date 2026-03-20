"""Vercel serverless function — post a template tweet."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from content import ContentGenerator
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

            query = parse_qs(urlparse(self.path).query)
            text = query.get("text", [None])[0]

            poster = TweetPoster(config)

            if text:
                tweet = text
            else:
                content = ContentGenerator(content_mix=config.content_mix, hashtags=config.hashtags)
                tweet = content.generate()

            success, result = poster.post(tweet)

            if success and log_post:
                log_post(tweet=tweet, source="template", tweet_id=result)

            self._respond(200 if success else 500, {
                "success": success,
                "tweet": tweet,
                "type": "template",
                "error": None if success else result,
            })
        except Exception as e:
            self._respond(500, {"error": str(e), "success": False})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
