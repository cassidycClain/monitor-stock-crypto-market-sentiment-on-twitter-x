from typing import Any, Dict, Iterable, List, Optional

def _numeric(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def apply_engagement_filters(
    tweets: Iterable[Dict[str, Any]],
    min_like_count: int = 0,
    min_retweet_count: int = 0,
    min_reply_count: int = 0,
    min_view_count: int = 0,
) -> List[Dict[str, Any]]:
    """
    Filter tweets by basic engagement metrics.
    """
    results: List[Dict[str, Any]] = []
    for tweet in tweets:
        if _numeric(tweet.get("likeCount")) < min_like_count:
            continue
        if _numeric(tweet.get("retweetCount")) < min_retweet_count:
            continue
        if _numeric(tweet.get("replyCount")) < min_reply_count:
            continue
        if _numeric(tweet.get("viewCount")) < min_view_count:
            continue
        results.append(tweet)
    return results

def filter_by_language(
    tweets: Iterable[Dict[str, Any]],
    lang: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if not lang:
        return list(tweets)
    lang = lang.lower()
    return [t for t in tweets if str(t.get("lang", "")).lower() == lang]

def filter_verified(
    tweets: Iterable[Dict[str, Any]],
    only_verified: bool = False,
    only_blue: bool = False,
) -> List[Dict[str, Any]]:
    if not (only_verified or only_blue):
        return list(tweets)

    results: List[Dict[str, Any]] = []
    for tweet in tweets:
        author = tweet.get("author") or {}
        is_verified = bool(author.get("isVerified"))
        # In this simple implementation, "blue" is approximated by verification.
        is_blue = is_verified

        if only_blue and not is_blue:
            continue
        if only_verified and not is_verified:
            continue

        results.append(tweet)
    return results

def sort_tweets(
    tweets: Iterable[Dict[str, Any]],
    sort_by: str = "likeCount",
    descending: bool = True,
) -> List[Dict[str, Any]]:
    data = list(tweets)
    if not data:
        return data

    def key_fn(t: Dict[str, Any]) -> Any:
        value = t.get(sort_by)
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    return sorted(data, key=key_fn, reverse=descending)

def apply_all_filters(
    tweets: Iterable[Dict[str, Any]],
    min_like_count: int = 0,
    min_retweet_count: int = 0,
    min_reply_count: int = 0,
    min_view_count: int = 0,
    lang: Optional[str] = None,
    only_verified: bool = False,
    only_blue: bool = False,
) -> List[Dict[str, Any]]:
    """
    Apply language, verification and engagement filters in a single pass.
    """
    step1 = filter_by_language(tweets, lang=lang)
    step2 = filter_verified(step1, only_verified=only_verified, only_blue=only_blue)
    step3 = apply_engagement_filters(
        step2,
        min_like_count=min_like_count,
        min_retweet_count=min_retweet_count,
        min_reply_count=min_reply_count,
        min_view_count=min_view_count,
    )
    return step3