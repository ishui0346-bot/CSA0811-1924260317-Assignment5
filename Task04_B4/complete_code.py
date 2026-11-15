"""B4 - Complete the Code (TODO 1 completed).
Run:  python Task04_B4/complete_code.py
"""
POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}

def score(text):
    """+1 per positive word, -1 per negative word; a preceding negator flips it."""
    words = text.lower().replace(".", " ").replace(",", " ").split()
    total = 0
    # TODO 1: For each word, find its value (+1, -1 or 0); if the previous word is a
    # negator, flip the sign; add it to total
    for i, w in enumerate(words):
        value = 1 if w in POSITIVE else -1 if w in NEGATIVE else 0
        if value and i > 0 and words[i - 1] in NEGATORS:
            value = -value
        total += value
    return total

def label(text):
    s = score(text)
    return "positive" if s > 0 else "negative" if s < 0 else "neutral"

for c in ["Roads are clean and the bus was fast.",
          "Smoke from the factory, air is bad.",
          "The staff were not helpful.",
          "Not bad, service improved."]:
    print(f"{label(c):8} | {c}")

# ---- A complaint the scorer labels WRONGLY, and why -------------------------------------------
wrong = "The staff were not at all helpful."
print(f"\nWrongly labelled: {label(wrong):8} | {wrong}")
print("Why: the negator 'not' is not DIRECTLY before 'helpful' ('at all' is in between), so the rule 'previous word is a"
      "\nnegator' misses it and 'helpful' counts as +1 -> positive. The scorer only looks one word back; sarcasm and"
      "\nmixed opinions also defeat it.")
