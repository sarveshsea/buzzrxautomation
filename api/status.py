"""Vercel serverless function — dashboard status endpoint."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
from content import ContentGenerator
from news import NewsReactor

try:
    from supabase_client import get_queue, get_usage, get_post_history
    HAS_SUPABASE = True
except Exception:
    HAS_SUPABASE = False


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
            headlines = reactor.fetch_headlines()

            result = {
                "status": "active" if creds_ok else "missing_credentials",
                "credentials": {
                    "twitter": creds_ok,
                    "openrouter": bool(config.openrouter_api_key),
                    "supabase": HAS_SUPABASE,
                },
                "templates": template_counts,
                "total_templates": sum(template_counts.values()),
                "new_headlines": len(headlines),
                "headlines": [h["title"] for h in headlines[:10]],
                "headlines_full": [{"title": h["title"], "source": h["source"], "link": h.get("link", ""), "image": h.get("image", "")} for h in headlines[:30]],
                "config": {
                    "posts_per_day": config.posts_per_day,
                    "active_hours": config.active_hours,
                    "media_chance": config.media_chance,
                },
            }

            if HAS_SUPABASE:
                result["usage"] = get_usage()
                result["queue"] = get_queue()
                result["recent_posts"] = get_post_history(limit=10)

            self._respond(200, result)
        except Exception as e:
            self._respond(500, {"error": str(e), "status": "error"})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
