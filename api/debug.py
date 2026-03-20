"""Debug endpoint — test if Vercel Python runtime works."""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = {"ok": True, "python": sys.version}

        # Check env vars
        data["env"] = {
            "TWITTER_API_KEY": bool(os.getenv("TWITTER_API_KEY")),
            "TWITTER_API_SECRET": bool(os.getenv("TWITTER_API_SECRET")),
            "TWITTER_ACCESS_TOKEN": bool(os.getenv("TWITTER_ACCESS_TOKEN")),
            "TWITTER_ACCESS_TOKEN_SECRET": bool(os.getenv("TWITTER_ACCESS_TOKEN_SECRET")),
            "TWITTER_BEARER_TOKEN": bool(os.getenv("TWITTER_BEARER_TOKEN")),
            "OPENROUTER_API_KEY": bool(os.getenv("OPENROUTER_API_KEY")),
        }

        # Check imports
        errors = []
        for mod in ["tweepy", "feedparser", "requests", "dotenv"]:
            try:
                __import__(mod)
            except ImportError as e:
                errors.append(f"{mod}: {e}")

        # Check our modules
        for mod in ["config", "content", "poster", "news", "media"]:
            try:
                __import__(mod)
            except Exception as e:
                errors.append(f"{mod}: {e}")

        data["import_errors"] = errors
        data["all_imports_ok"] = len(errors) == 0

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
