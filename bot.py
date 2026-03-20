#!/usr/bin/env python3
"""Buzzr X Automation Bot — CLI entry point."""

import argparse
import logging
import sys

from config import Config
from content import ContentGenerator
from media import MediaManager
from news import NewsReactor
from poster import TweetPoster
from scheduler import TweetScheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def cmd_run(args):
    """Run the scheduled posting bot."""
    config = Config()
    dry_run = args.dry_run or config.dry_run

    if not dry_run and not config.validate():
        print("\n⚠️  Missing API credentials. Add them to your .env file.")
        print("   Or use --dry-run to test without posting.\n")
        sys.exit(1)

    content = ContentGenerator(
        content_mix=config.content_mix,
        hashtags=config.hashtags,
    )
    media = MediaManager(media_chance=config.media_chance)
    poster = TweetPoster(config)
    scheduler = TweetScheduler(poster, content, config, media_manager=media)
    scheduler.run(dry_run=dry_run)


def cmd_post(args):
    """Post a single tweet now."""
    config = Config()
    dry_run = args.dry_run or config.dry_run

    if not dry_run and not config.validate():
        print("\n⚠️  Missing API credentials. Add them to your .env file.\n")
        sys.exit(1)

    content = ContentGenerator(
        content_mix=config.content_mix,
        hashtags=config.hashtags,
    )
    media = MediaManager(media_chance=config.media_chance)
    poster = TweetPoster(config)

    if args.text:
        tweet = args.text
    else:
        category = args.category if args.category else None
        tweet = content.generate(category=category)

    media_path = None if args.no_media else media.pick_media()
    print(f"\n📝 Tweet ({len(tweet)} chars):\n{tweet}")
    if media_path:
        print(f"   📎 Media: {media_path.name}")
    print()
    poster.post(tweet, media_path=media_path, dry_run=dry_run)


def cmd_preview(args):
    """Preview generated tweets without posting."""
    config = Config()
    content = ContentGenerator(
        content_mix=config.content_mix,
        hashtags=config.hashtags,
    )

    if args.all:
        templates = content.preview_all()
        for category, tweets in templates.items():
            print(f"\n{'='*60}")
            print(f"  {category.upper()} ({len(tweets)} templates)")
            print(f"{'='*60}")
            for i, tweet in enumerate(tweets, 1):
                print(f"\n  [{i}] {tweet}")
        total = sum(len(t) for t in templates.values())
        print(f"\n📊 Total templates: {total}\n")
    else:
        count = args.count or 5
        print(f"\n🔮 Previewing {count} random tweets:\n")
        for i, tweet in enumerate(content.preview(count), 1):
            print(f"  [{i}] ({len(tweet)} chars)")
            print(f"  {tweet}\n")


def cmd_react(args):
    """React to latest sports news with an AI-generated tweet."""
    config = Config()
    dry_run = args.dry_run or config.dry_run

    if not dry_run and not config.validate():
        print("\n⚠️  Missing API credentials. Add them to your .env file.\n")
        sys.exit(1)

    reactor = NewsReactor(
        openrouter_api_key=config.openrouter_api_key,
        model=config.openrouter_model,
    )
    media = MediaManager(media_chance=config.media_chance)
    poster = TweetPoster(config)

    tweet, article = reactor.get_reactive_tweet()
    if not tweet:
        print("\n📰 No new sports headlines to react to right now.\n")
        return

    media_path = media.pick_media()
    print(f"\n📰 Reacting to: {article['title']}")
    print(f"   Source: {article['source']}")
    print(f"\n📝 Tweet ({len(tweet)} chars):\n{tweet}")
    if media_path:
        print(f"   📎 Media: {media_path.name}")
    print()
    poster.post(tweet, media_path=media_path, dry_run=dry_run)


def cmd_test_auth(args):
    """Test API authentication."""
    config = Config()
    if not config.validate():
        print("\n⚠️  Missing API credentials in .env file.")
        print("   Fill in: TWITTER_API_KEY, TWITTER_API_SECRET,")
        print("   TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET\n")
        return

    poster = TweetPoster(config)
    poster.test_auth()


def main():
    parser = argparse.ArgumentParser(
        description="🐝 Buzzr X Automation Bot — Tweet about Buzzr on autopilot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run
    run_parser = subparsers.add_parser("run", help="Start scheduled posting")
    run_parser.add_argument("--dry-run", action="store_true", help="Simulate without posting")
    run_parser.set_defaults(func=cmd_run)

    # post
    post_parser = subparsers.add_parser("post", help="Post a single tweet")
    post_parser.add_argument("--text", type=str, help="Custom tweet text")
    post_parser.add_argument("--category", choices=["promo", "features", "engagement", "tips"])
    post_parser.add_argument("--no-media", action="store_true", help="Skip media attachment")
    post_parser.add_argument("--dry-run", action="store_true", help="Simulate without posting")
    post_parser.set_defaults(func=cmd_post)

    # react
    react_parser = subparsers.add_parser("react", help="React to sports news with AI tweet")
    react_parser.add_argument("--dry-run", action="store_true", help="Simulate without posting")
    react_parser.set_defaults(func=cmd_react)

    # preview
    preview_parser = subparsers.add_parser("preview", help="Preview tweets without posting")
    preview_parser.add_argument("--all", action="store_true", help="Show all templates")
    preview_parser.add_argument("--count", type=int, default=5, help="Number of random previews")
    preview_parser.set_defaults(func=cmd_preview)

    # test-auth
    auth_parser = subparsers.add_parser("test-auth", help="Test API authentication")
    auth_parser.set_defaults(func=cmd_test_auth)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
