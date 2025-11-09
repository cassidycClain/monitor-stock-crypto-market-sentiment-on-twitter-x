import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

class TwitterScraper:
    """
    Lightweight client for the Twitter/X v2 recent search endpoint.

    It is intentionally minimal and focuses on cashtag queries with basic
    author and engagement metadata.
    """

    def __init__(self, bearer_token: str, base_url: str = "https://api.twitter.com/2/tweets/search/recent") -> None:
        if not bearer_token:
            raise ValueError("A valid Twitter API bearer token is required.")
        self._bearer_token = bearer_token
        self._base_url = base_url
        self._session = requests.Session()

    @staticmethod
    def _build_query(symbols: List[str]) -> str:
        if not symbols:
            raise ValueError("At least one cashtag symbol is required.")

        cashtag_terms: List[str] = []
        for raw in symbols:
            if not raw:
                continue
            symbol = raw.strip()
            if symbol.startswith("$"):
                symbol = symbol[1:]
            if not symbol:
                continue
            cashtag_terms.append(f"(${symbol.upper()})")

        if not cashtag_terms:
            raise ValueError("No valid cashtag symbols were provided.")

        combined = " OR ".join(cashtag_terms)
        # Exclude retweets and replies for cleaner sentiment
        return f"({combined}) -is:retweet -is:reply"

    def search_cashtags(
        self,
        symbols: List[str],
        max_results: int = 50,
        lang: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        only_verified: bool = False,
        only_blue: bool = False,
    ) -> List[Dict]:
        """
        Search for recent tweets containing one or more cashtags.

        :param symbols: List of cashtag symbols without the leading '$', e.g. ["BTC", "AAPL"].
        :param max_results: Maximum results to ask from the API (10-100).
        :param lang: Optional BCP47 language code filter (e.g. "en").
        :param start_time: RFC 3339/ISO 8601 timestamp string limiting from when to search.
        :param end_time: RFC 3339/ISO 8601 timestamp string limiting up to when to search.
        :param only_verified: If True, only return tweets from verified accounts.
        :param only_blue: If True, prefer users that are Twitter Blue (approximated via verification flag).
        """
        query = self._build_query(symbols)
        max_results = max(10, min(int(max_results), 100))

        params: Dict[str, str] = {
            "query": query,
            "max_results": str(max_results),
            "tweet.fields": "created_at,lang,public_metrics,referenced_tweets,author_id",
            "expansions": "author_id,referenced_tweets.id",
            "user.fields": "name,username,verified,public_metrics",
        }

        if lang:
            params["query"] = f"{params['query']} lang:{lang}"

        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time

        headers = {"Authorization": f"Bearer {self._bearer_token}"}

        logger.debug("Requesting Twitter API with params: %s", params)

        try:
            response = self._session.get(self._base_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Error while calling Twitter API: %s", exc)
            raise

        payload = response.json()
        data = payload.get("data", [])
        includes = payload.get("includes", {})

        users_index: Dict[str, Dict] = {u.get("id"): u for u in includes.get("users", [])}
        quoted_index: Dict[str, Dict] = {t.get("id"): t for t in includes.get("tweets", [])}

        results: List[Dict] = []
        for item in data:
            public_metrics = item.get("public_metrics", {}) or {}
            author_id = item.get("author_id")
            raw_author = users_index.get(author_id, {}) or {}
            author_metrics = raw_author.get("public_metrics", {}) or {}

            username = raw_author.get("username") or "unknown"
            tweet_id = item.get("id")

            tweet_url = f"https://x.com/{username}/status/{tweet_id}" if username and tweet_id else None

            quote = None
            for ref in item.get("referenced_tweets", []) or []:
                if ref.get("type") == "quoted":
                    quoted = quoted_index.get(ref.get("id"))
                    if quoted:
                        quote = {
                            "id": quoted.get("id"),
                            "text": quoted.get("text"),
                        }
                        break

            # Basic verification flags
            is_verified = bool(raw_author.get("verified"))
            # We don't have explicit "blue" information in this minimal example; approximate with verified.
            is_blue = is_verified

            if only_verified and not is_verified:
                continue
            if only_blue and not is_blue:
                continue

            result = {
                "type": "tweet",
                "id": tweet_id,
                "url": tweet_url,
                "text": item.get("text", ""),
                # sentiment will be filled by the sentiment analyzer later
                "sentiment": "NEUTRAL",
                "retweetCount": int(public_metrics.get("retweet_count", 0)),
                "replyCount": int(public_metrics.get("reply_count", 0)),
                "likeCount": int(public_metrics.get("like_count", 0)),
                "viewCount": int(
                    public_metrics.get("impression_count", public_metrics.get("view_count", 0))
                ),
                "createdAt": item.get("created_at"),
                "lang": item.get("lang"),
                "author": {
                    "userName": username,
                    "name": raw_author.get("name"),
                    "isVerified": is_verified,
                    "followers": int(author_metrics.get("followers_count", 0)),
                },
                "quote": quote,
            }

            results.append(result)

        logger.info("Fetched %d tweets from Twitter API", len(results))
        return results