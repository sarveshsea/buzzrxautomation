"""Vercel serverless function — dashboard status endpoint."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from content import ContentGenerator
from news import NewsReactor


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            config = Config()
            creds_ok = config.validate()

            content = ContentGenerator(content_mix=config.content_mix, hashtags=config.hashtags)
            templates = content.preview_all()
            template_counts = {k: len(v) for k, v in templates.items()}

            reactor = NewsReactor(
                openrouter_api_key=config.openrouter_api_key,
                model=config.openrouter_model,
            )
            headlines = reactor.fetch_new_headlines()

            self._respond(200, {
                "status": "active" if creds_ok else "missing_credentials",
                "credentials": {
                    "twitter": creds_ok,
                    "openrouter": bool(config.openrouter_api_key),
                },
                "templates": template_counts,
                "total_templates": sum(template_counts.values()),
                "new_headlines": len(headlines),
                "headlines": [h["title"] for h in headlines[:5]],
                "config": {
                    "posts_per_day": config.posts_per_day,
                    "active_hours": config.active_hours,
                    "media_chance": config.media_chance,
                },
            })
        except Exception as e:
            self._respond(500, {"error": str(e), "status": "error"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
