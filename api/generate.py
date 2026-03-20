"""Vercel serverless function — generate AI tweet from a headline (no post)."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from news import NewsReactor


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            query = parse_qs(urlparse(self.path).query)
            headline = query.get("headline", [""])[0]
            if not headline:
                self._respond(400, {"error": "Missing ?headline= parameter"})
                return

            config = Config()
            reactor = NewsReactor(
                openrouter_api_key=config.openrouter_api_key,
                model=config.openrouter_model,
            )
            tweet = reactor.generate_reactive_tweet(headline, "")
            self._respond(200, {"success": True, "tweet": tweet, "headline": headline})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
