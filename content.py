"""Tweet content generator for Buzzr — 50+ templates across 4 categories."""

import random
from datetime import datetime

PROMO_TWEETS = [
    "Rotten Tomatoes, but for sports. Rate every game 1-10 and see if your takes hold up. That's Buzzr. 🏀🔥",
    "Stop yelling at your TV alone. Buzzr lets you rate games, earn badges, and prove your sports IQ. Download now.",
    "Your sports opinions finally have a home. Buzzr — rate games, track takes, flex on friends.",
    "Buzzr turns every game into a conversation. Rate it. Rank it. See where you stand.",
    "Think last night's game was a 10? Prove it. Rate every game on Buzzr and build your reputation.",
    "Sports fans deserve better than group chats. Buzzr gives your takes a stage.",
    "Every game. Every take. Every badge earned. Buzzr is where real fans show up.",
    "Your friend says that game was mid? Challenge their rating on Buzzr. Let the numbers talk.",
    "Buzzr: where your hot takes become your track record. Rate games. Earn badges. Climb the leaderboard.",
    "The game doesn't end at the final whistle. It ends when you rate it on Buzzr.",
    "If you're not rating games on Buzzr, are you even watching? 👀",
    "Buzzr is the scoreboard for your sports brain. How good are your takes really?",
    "We built Buzzr because sports opinions deserved more than a tweet. They deserve a rating system.",
]

FEATURE_TWEETS = [
    "🏅 Badge drop: 'First Whistle' — be the first to rate a game and wear it proud on your Buzzr profile.",
    "The Buzzer Beater badge goes to fans who rate games in the final minutes. Clutch recognizes clutch. ⏰",
    "Night Owl badge: for the real ones still rating West Coast games at 1am. Buzzr sees you. 🦉",
    "Got a take nobody agrees with? The Contrarian badge on Buzzr means you're not afraid to stand alone.",
    "Watch Events on Buzzr = watching the game with thousands of fans rating in real time. Join one tonight.",
    "Trending Games on Buzzr shows you what the sports world is buzzing about right now. Never miss the hype.",
    "The Hot Take Leaderboard ranks the boldest raters on Buzzr. Think you can crack the top 10?",
    "Follow your friends on Buzzr and see their ratings in real time. Finally, accountability for bad takes.",
    "Buzzr's 1-10 rating system is simple on purpose. No essays needed — just your honest score.",
    "Your Buzzr profile is your sports resume. Every rating, every badge, every take — all in one place.",
    "Game just ended? Buzzr shows live rating distributions so you can see where fans stand.",
    "Buzzr's algorithm surfaces the most debated games. If ratings are split, you know it was a wild one.",
]

ENGAGEMENT_TWEETS = [
    "What's your most controversial sports rating? Drop it below. 👇",
    "Rate the game tonight 1-10. Wrong answers only. 😂",
    "Hot take: a 7/10 game is the most underrated score. It means 'good but something was off.' Agree?",
    "What sport has the most 10/10 games? NBA? NFL? Soccer? Make your case.",
    "If you could only rate one sport for the rest of your life, what are you picking?",
    "The worst feeling: rating a game a 9 and watching everyone else give it a 5. Been there? 😅",
    "Who's the most polarizing team in sports right now? The Buzzr ratings don't lie.",
    "Game of the year so far? Drop the name and your Buzzr rating. Let's see if we agree.",
    "Unpopular opinion: blowouts can still be 8/10 games if one team plays perfect. Thoughts?",
    "Your friend group's average Buzzr rating says a lot about your sports taste. What's yours?",
    "If sports games were movies, what game would be a perfect 10/10? 🎬🏆",
    "Monday morning debate: was last night actually good or did we just want it to be?",
    "Tell me your Buzzr rating for the last game you watched. No context, just the number.",
]

TIPS_TWEETS = [
    "Pro tip: rate games right after they end while the energy is fresh. Your Buzzr ratings will be more honest.",
    "Buzzr tip: follow at least 10 friends to unlock the best part — comparing ratings after every game.",
    "New to Buzzr? Start by rating tonight's biggest game. One rating and you're in the community.",
    "Want to climb the Buzzr leaderboard? Consistency > volume. Rate every game you actually watch.",
    "Buzzr hack: check Trending Games before the weekend to plan what to watch. Community-curated schedule.",
    "The best Buzzr profiles have 50+ ratings. That's when patterns emerge and your sports identity forms.",
    "Don't sleep on Watch Events. Rating with a crowd hits different than rating alone.",
    "Buzzr tip: your first rating sets the tone. Don't overthink it — go with your gut.",
    "Sports are better with stakes. Make a Buzzr bet with friends: closest to the final average rating wins.",
    "The secret to Buzzr: it's not about being right. It's about having a take and owning it.",
    "Building your Buzzr streak? Rate at least one game every day this week. Badge hunters know the drill.",
    "Buzzr tip: tap on any game to see the rating breakdown. The distribution tells you more than the average.",
]

ALL_CATEGORIES = {
    "promo": PROMO_TWEETS,
    "features": FEATURE_TWEETS,
    "engagement": ENGAGEMENT_TWEETS,
    "tips": TIPS_TWEETS,
}


class ContentGenerator:
    """Generates tweet content based on configured content mix."""

    def __init__(self, content_mix=None, hashtags=None):
        self.content_mix = content_mix or {
            "promo": 0.30,
            "features": 0.25,
            "engagement": 0.30,
            "tips": 0.15,
        }
        self.hashtags = hashtags or ["#Buzzr", "#SportsApp"]
        self._used_tweets = set()

    def generate(self, category=None):
        """Generate a tweet. Optionally specify a category."""
        if category is None:
            category = self._pick_category()

        tweets = ALL_CATEGORIES.get(category, PROMO_TWEETS)
        available = [t for t in tweets if t not in self._used_tweets]

        if not available:
            self._used_tweets -= set(tweets)
            available = tweets

        tweet = random.choice(available)
        self._used_tweets.add(tweet)

        # Add 1-2 random hashtags (50% chance)
        if random.random() > 0.5 and self.hashtags:
            tags = random.sample(self.hashtags, min(2, len(self.hashtags)))
            tweet = f"{tweet}\n\n{' '.join(tags)}"

        # Ensure tweet is within 280 chars
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."

        return tweet

    def _pick_category(self):
        """Weighted random category selection based on content_mix."""
        categories = list(self.content_mix.keys())
        weights = list(self.content_mix.values())
        return random.choices(categories, weights=weights, k=1)[0]

    def preview_all(self):
        """Return all templates grouped by category."""
        return ALL_CATEGORIES

    def preview(self, count=5):
        """Preview N random tweets."""
        return [self.generate() for _ in range(count)]
