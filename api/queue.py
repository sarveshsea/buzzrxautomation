"""Vercel serverless function — shared queue CRUD via Supabase."""
from http.server import BaseHTTPRequestHandler
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from news import NewsReactor
from supabase_client import (
    get_queue, add_to_queue, update_queue_item,
    remove_from_queue, clear_queue, get_usage,
)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """GET /api/queue — list queue + usage stats."""
        try:
            items = get_queue()
            usage = get_usage()
            self._respond(200, {
                "success": True,
                "queue": items,
                "usage": usage,
            })
        except Exception as e:
            self._respond(500, {"error": str(e), "success": False})

    def do_POST(self):
        """POST /api/queue — add to queue, generate tweet, or actions."""
        try:
            query = parse_qs(urlparse(self.path).query)
            action = query.get("action", ["add"])[0]

            if action == "add":
                headline = query.get("headline", [""])[0]
                if not headline:
                    self._respond(400, {"error": "Missing ?headline=", "success": False})
                    return
                item = add_to_queue(headline)
                if not item:
                    self._respond(500, {"error": "Failed to add to queue", "success": False})
                    return

                # Generate AI tweet
                config = Config()
                reactor = NewsReactor(
                    openrouter_api_key=config.openrouter_api_key,
                    model=config.openrouter_model,
                )
                tweet = reactor.generate_reactive_tweet(headline, "")
                update_queue_item(item["id"], tweet=tweet, status="ready")
                item["tweet"] = tweet
                item["status"] = "ready"
                self._respond(200, {"success": True, "item": item})

            elif action == "regenerate":
                item_id = query.get("id", [""])[0]
                headline = query.get("headline", [""])[0]
                if not item_id or not headline:
                    self._respond(400, {"error": "Missing ?id= and ?headline=", "success": False})
                    return
                config = Config()
                reactor = NewsReactor(
                    openrouter_api_key=config.openrouter_api_key,
                    model=config.openrouter_model,
                )
                tweet = reactor.generate_reactive_tweet(headline, "")
                update_queue_item(int(item_id), tweet=tweet, status="ready")
                self._respond(200, {"success": True, "tweet": tweet})

            elif action == "remove":
                item_id = query.get("id", [""])[0]
                if not item_id:
                    self._respond(400, {"error": "Missing ?id=", "success": False})
                    return
                remove_from_queue(int(item_id))
                self._respond(200, {"success": True})

            elif action == "clear":
                clear_queue()
                self._respond(200, {"success": True})

            else:
                self._respond(400, {"error": f"Unknown action: {action}", "success": False})

        except Exception as e:
            self._respond(500, {"error": str(e), "success": False})

    def _respond(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
