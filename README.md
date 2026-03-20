# Buzzr X Automation Bot 🐝

Auto-post tweets promoting [Buzzr](https://getbuzzr.com) — the Rotten Tomatoes for sports.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd ~/Desktop/buzzrxautomation
   pip install -r requirements.txt
   ```

2. **Add your API keys** to `.env`:
   - Go to [X Developer Portal](https://developer.x.com/en/portal/dashboard)
   - Navigate to your app > Keys and Tokens
   - Copy API Key, API Secret, Access Token, and Access Token Secret into `.env`

3. **Test authentication:**
   ```bash
   python bot.py test-auth
   ```

4. **Preview tweets:**
   ```bash
   python bot.py preview           # 5 random tweets
   python bot.py preview --all     # all 50+ templates
   ```

5. **Post a single tweet:**
   ```bash
   python bot.py post              # random tweet
   python bot.py post --category promo
   python bot.py post --text "Custom tweet here"
   python bot.py post --dry-run    # simulate without posting
   ```

6. **Start the scheduled bot:**
   ```bash
   python bot.py run               # posts 4x/day during active hours
   python bot.py run --dry-run     # simulate the schedule
   ```

## Configuration

Edit `config.json` to customize:
- `posts_per_day` — how many tweets per day (default: 4)
- `active_hours` — when to post (default: 9am–11pm)
- `content_mix` — weight of each category (promo, features, engagement, tips)
- `hashtags` — hashtags randomly appended to tweets
- `dry_run` — set to `true` to test without posting

## Content Categories

- **Promo** (30%) — App promotion and downloads
- **Features** (25%) — Badges, Watch Events, Leaderboard, etc.
- **Engagement** (30%) — Questions and community interaction
- **Tips** (15%) — How to get the most out of Buzzr

## Project Structure

```
buzzrxautomation/
├── bot.py          # CLI entry point
├── config.py       # Credential & settings loader
├── config.json     # Posting settings
├── content.py      # 50+ tweet templates
├── poster.py       # Twitter API integration
├── scheduler.py    # Timed posting logic
├── requirements.txt
├── .env            # Your API keys (gitignored)
├── .env.example    # Template for .env
└── .gitignore
```
