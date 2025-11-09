import logging
import re
from typing import Literal

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

SentimentLabel = Literal["BULLISH", "BEARISH", "NEUTRAL"]

class SentimentAnalyzer:
    """
    Simple financial sentiment classifier built on top of VADER.

    It combines the VADER compound score with a few finance-specific keyword
    boosts to label tweets as BULLISH, BEARISH, or NEUTRAL.
    """

    BULLISH_KEYWORDS = (
        r"\b(call|calls|long|buy|bought|adding|accumulating|moon|pump|bull|bullish|breakout|rally)\b",
    )
    BEARISH_KEYWORDS = (
        r"\b(put|puts|short|sell|sold|dump|bear|bearish|crash|collapse|rug)\b",
    )

    def __init__(self) -> None:
        self._analyzer = SentimentIntensityAnalyzer()
        self._bullish_re = re.compile("|".join(self.BULLISH_KEYWORDS), flags=re.IGNORECASE)
        self._bearish_re = re.compile("|".join(self.BEARISH_KEYWORDS), flags=re.IGNORECASE)

    def classify(self, text: str) -> SentimentLabel:
        """
        Classify raw text into one of BULLISH, BEARISH, or NEUTRAL.
        """
        if not text or not text.strip():
            return "NEUTRAL"

        text = text.strip()
        scores = self._analyzer.polarity_scores(text)
        compound = scores.get("compound", 0.0)

        # Base VADER thresholds
        bullish = compound >= 0.25
        bearish = compound <= -0.25

        # Keyword reinforcement
        if self._bullish_re.search(text):
            bullish = True
        if self._bearish_re.search(text):
            bearish = True

        if bullish and not bearish:
            label: SentimentLabel = "BULLISH"
        elif bearish and not bullish:
            label = "BEARISH"
        else:
            label = "NEUTRAL"

        logger.debug("Classified sentiment '%s' with compound=%.3f as %s", text, compound, label)
        return label