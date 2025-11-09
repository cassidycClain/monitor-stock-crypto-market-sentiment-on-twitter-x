import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

from sentiment_analyzer import SentimentAnalyzer
from twitter_scraper import TwitterScraper
from utils.config_loader import load_settings, load_credentials
from utils.filters import apply_all_filters, sort_tweets

def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger = logging.getLogger("cashtag_monitor")

    try:
        settings = load_settings()
        credentials = load_credentials()
    except FileNotFoundError as exc:
        logger.error("Configuration file not found: %s", exc)
        return
    except ValueError as exc:
        logger.error("Failed to parse configuration: %s", exc)
        return

    bearer_token = credentials.get("twitter", {}).get("bearerToken")
    if not bearer_token:
        logger.error("Missing twitter.bearerToken in credentials configuration.")
        return

    symbols = settings.get("symbols") or []
    if not symbols:
        logger.error("No cashtag symbols configured. Add at least one symbol in settings.json.")
        return

    scraper = TwitterScraper(bearer_token=bearer_token)
    analyzer = SentimentAnalyzer()

    since_minutes = int(settings.get("sinceMinutes", 60))
    now = datetime.now(timezone.utc)
    start_time = (now - timedelta(minutes=since_minutes)).isoformat().replace("+00:00", "Z")

    lang = settings.get("lang") or None

    logger.info(
        "Fetching tweets for symbols %s (since %d minutes ago, lang=%s)...",
        ", ".join(symbols),
        since_minutes,
        lang or "any",
    )

    try:
        tweets = scraper.search_cashtags(
            symbols=symbols,
            max_results=int(settings.get("maxResults", 50)),
            lang=lang,
            start_time=start_time,
            only_verified=bool(settings.get("onlyVerifiedUsers", False)),
            only_blue=bool(settings.get("onlyTwitterBlue", False)),
        )
    except Exception as exc:  # network or API errors
        logger.error("Error while fetching tweets: %s", exc)
        return

    if not tweets:
        logger.warning("No tweets returned by the API.")
        return

    for tweet in tweets:
        text = tweet.get("text") or ""
        tweet["sentiment"] = analyzer.classify(text)

    filtered = apply_all_filters(
        tweets,
        min_like_count=int(settings.get("minLikeCount", 0)),
        min_retweet_count=int(settings.get("minRetweetCount", 0)),
        min_reply_count=int(settings.get("minReplyCount", 0)),
        min_view_count=int(settings.get("minViewCount", 0)),
        lang=lang,
        only_verified=bool(settings.get("onlyVerifiedUsers", False)),
        only_blue=bool(settings.get("onlyTwitterBlue", False)),
    )

    sort_by = settings.get("sortBy", "likeCount")
    sort_order = str(settings.get("sortOrder", "desc")).lower()
    descending = sort_order != "asc"
    filtered = sort_tweets(filtered, sort_by=sort_by, descending=descending)

    output_file = settings.get("outputFile", "data/sample_output.json")
    project_root = Path(__file__).resolve().parents[1]
    output_path = (project_root / output_file).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

    logger.info("Wrote %d tweets to %s", len(filtered), output_path)

if __name__ == "__main__":
    run()