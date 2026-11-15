"""Lexicon sentiment scorer + extractive summariser (implements A5.1)."""
import re
from collections import Counter

POSITIVE = {"good", "clean", "fast", "helpful", "improved", "great", "excellent", "friendly",
            "better", "quick", "fresh", "polite", "thank", "thanks", "happy", "pleasant", "love", "best"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken", "worse", "terrible", "awful",
            "polluted", "toxic", "stink", "smell", "dust", "noise", "choking", "cough", "worst",
            "unsafe", "ignored", "delay", "delayed", "burning", "garbage"}
NEGATORS = {"not", "never", "no", "hardly", "cannot", "cant", "isnt", "wasnt", "dont", "didnt"}
STOPWORDS = set("""a an and are as at be been but by for from has have in is it its of on or
that the their there they this to was were will with we our you your i my me so very too also
than then them these those over after before again just""".split())


def tokenize(text):
    return re.findall(r"[a-z]+", text.lower().replace("'", ""))


def score(text):
    words = tokenize(text)
    total = 0
    for i, w in enumerate(words):
        v = 1 if w in POSITIVE else -1 if w in NEGATIVE else 0
        if v and i > 0 and words[i - 1] in NEGATORS:
            v = -v
        total += v
    return total


def label(text):
    s = score(text)
    return "positive" if s > 0 else "negative" if s < 0 else "neutral"


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def summarise(text, k=1):
    """Pick the k sentences with the highest sum of frequencies of important words."""
    sents = split_sentences(text)
    if len(sents) <= k:
        return sents
    freq = Counter(w for w in tokenize(text) if w not in STOPWORDS)
    scored = [(sum(freq[w] for w in tokenize(s) if w not in STOPWORDS), i) for i, s in enumerate(sents)]
    top = sorted(sorted(scored, key=lambda x: (-x[0], x[1]))[:k], key=lambda x: x[1])
    return [sents[i] for _, i in top]


def first_k(text, k=1):
    return split_sentences(text)[:k]
