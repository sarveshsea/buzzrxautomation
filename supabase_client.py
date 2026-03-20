"""Lightweight Supabase REST client — no SDK dependency."""

import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def _url(table):
    return f"{SUPABASE_URL}/rest/v1/{table}"


# ── Queue ──────────────────────────────────────────────

def get_queue():
    """Get all pending/ready queue items, ordered by id."""
    r = requests.get(
        _url("queue") + "?status=in.(pending,generating,ready)&order=id.asc",
        headers=HEADERS, timeout=10,
    )
    return r.json() if r.ok else []


def add_to_queue(headline, created_by=None):
    """Add a headline to the queue."""
    r = requests.post(
        _url("queue"),
        headers=HEADERS, timeout=10,
        json={"headline": headline, "status": "pending", "created_by": created_by},
    )
    return r.json()[0] if r.ok else None


def update_queue_item(item_id, **fields):
    """Update a queue item (tweet, status, etc)."""
    r = requests.patch(
        _url("queue") + f"?id=eq.{item_id}",
        headers=HEADERS, timeout=10,
        json=fields,
    )
    return r.ok


def remove_from_queue(item_id):
    """Delete a queue item."""
    r = requests.delete(
        _url("queue") + f"?id=eq.{item_id}",
        headers=HEADERS, timeout=10,
    )
    return r.ok


def clear_queue():
    """Delete all non-posted queue items."""
    r = requests.delete(
        _url("queue") + "?status=in.(pending,generating,ready)",
        headers=HEADERS, timeout=10,
    )
    return r.ok


# ── Post History ───────────────────────────────────────

def log_post(tweet, headline=None, source=None, tweet_id=None, cost=0.0130):
    """Log a posted tweet and its cost."""
    r = requests.post(
        _url("post_history"),
        headers=HEADERS, timeout=10,
        json={
            "tweet": tweet,
            "headline": headline,
            "source": source,
            "tweet_id": tweet_id,
            "cost_estimate": cost,
        },
    )
    return r.ok


def get_post_history(limit=20):
    """Get recent post history."""
    r = requests.get(
        _url("post_history") + f"?order=posted_at.desc&limit={limit}",
        headers=HEADERS, timeout=10,
    )
    return r.json() if r.ok else []


# ── Usage / Balance ────────────────────────────────────

def get_usage():
    """Get balance info: initial balance, cost per post, total spent, remaining."""
    # Get the usage config
    r = requests.get(
        _url("usage") + "?limit=1",
        headers=HEADERS, timeout=10,
    )
    usage = r.json()[0] if r.ok and r.json() else {"initial_balance": 5.0, "cost_per_post": 0.013}

    # Count total spent from post_history
    r2 = requests.get(
        _url("post_history") + "?select=cost_estimate",
        headers=HEADERS, timeout=10,
    )
    posts = r2.json() if r2.ok else []
    total_spent = sum(float(p.get("cost_estimate", 0.013)) for p in posts)
    total_posts = len(posts)

    initial = float(usage.get("initial_balance", 5.0))
    cost_per = float(usage.get("cost_per_post", 0.013))
    remaining = max(initial - total_spent, 0)
    posts_remaining = int(remaining / cost_per) if cost_per > 0 else 0

    return {
        "initial_balance": initial,
        "total_spent": round(total_spent, 4),
        "remaining": round(remaining, 4),
        "total_posts": total_posts,
        "cost_per_post": cost_per,
        "posts_remaining": posts_remaining,
    }


def check_spending_cap(cap=0.50):
    """Returns True if balance is above the cap, False if we should stop posting."""
    usage = get_usage()
    return usage["remaining"] > cap
