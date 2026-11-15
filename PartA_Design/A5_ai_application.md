# A5: Design an AI Application for Citizen Complaints (4 marks, K3)

## A5.1 Sentiment and summary (2)
**Lexicon scorer with negation** (implemented in `shared/sentiment.py`, B4)
```
ALGORITHM Score(text)
  words <- LOWERCASE(text) split into words (letters only)
  total <- 0
  FOR i FROM 0 TO LENGTH(words) - 1 DO
     v <- +1 IF words[i] IN POSITIVE;  -1 IF words[i] IN NEGATIVE;  ELSE 0
     IF v ≠ 0 AND i > 0 AND words[i-1] IN NEGATORS THEN v <- -v      // "not good" -> -1
     total <- total + v
  RETURN total
ALGORITHM Label(text): s <- Score(text); RETURN "positive" IF s>0, "negative" IF s<0, ELSE "neutral"
```
**Extractive summariser**
```
ALGORITHM Summarise(text, k)
  sentences <- SPLIT_SENTENCES(text)
  freq <- COUNT of each word in text that is NOT a stop-word
  FOR EACH sentence s: weight[s] <- SUM(freq[w] FOR w IN s IF w NOT stop-word)
  chosen <- the k sentences with the largest weight
  RETURN chosen in their ORIGINAL order
```
Limits: scorer looks only one word back; ignores sarcasm, scope of negation, intensity and unknown words. Summariser favours long
sentences and cannot rephrase.

## A5.2 Basic chatbot (2)
```
ALGORITHM Chatbot(question)
  q <- LOWERCASE(question)
  station <- FIRST station name found in q               // keyword match against stations table
  IF "pm2.5" IN q OR "air" IN q THEN
     day <- "today" -> CURRENT_DATE ; "yesterday" -> CURRENT_DATE - 1
     row <- EXECUTE "SELECT ROUND(AVG(pm25),1) FROM readings WHERE station_id=? AND day=?" (id, day)   // placeholders!
     IF station NOT FOUND THEN RETURN "Which station?"
     IF row IS NULL THEN RETURN "No data for <station> on <day>"
     RETURN "PM2.5 in <station> on <day> is <value> µg/m³ (<category>)"
  ELSE IF "worst" IN q THEN RETURN hour/station with the highest average
  ELSE RETURN help text listing what I can answer
```
**Limitations:** only known keywords and station names (spelling mistakes, synonyms, other languages fail); no context across
turns ("and yesterday?"); cannot answer why/forecast questions; depends on up-to-date data; health advice must come from fixed text,
not be invented.

## Alternative concept and complexity analysis
**Alternative:** a trained model (Naive Bayes on word counts, or a pre-trained language model) instead of a word list.
```
ALGORITHM TrainNaiveBayes(labelled)   // once: count words per class, priors
ALGORITHM Predict(text): argmax over classes of LOG(prior) + SUM(LOG P(word | class))
```
| | Word list | Naive Bayes | Pre-trained language model |
|---|---|---|---|
| Time per complaint | O(words), ~3 µs measured (B4) | O(words × classes), ~10-50 µs | milliseconds to 100s of ms (CPU) |
| Memory | a few KB | MBs (vocabulary × classes) | 100 MB - GBs |
| Accuracy | 84 % on my 51 labelled complaints (optimistic), fails on sarcasm/negation scope | usually better *if* it has enough labelled data (hundreds+) | best on context, negation, sarcasm |
| Needs | nothing | labelled data, training step | library, model download, more compute |
