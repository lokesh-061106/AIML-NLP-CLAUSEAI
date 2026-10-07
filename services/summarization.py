import re

LEGAL_WORDS = {
    'agreement', 'party', 'parties',
    'obligation', 'payment', 'notice',
    'termination', 'terminate',
    'liability', 'indemnification',
    'confidential', 'breach',
    'jurisdiction', 'arbitration',
    'damages', 'claims', 'losses',
    'warranty', 'renewal'
}

def split_sentences(text):
    text = re.sub(r'\s+', ' ', text or '').strip()
    if not text:
        return []
    return [
        x.strip()
        for x in re.split(r'(?<=[.!?])\s+', text)
        if x.strip()
    ]

def sentence_score(sentence, index, total):
    words = re.findall(r'\b\w+\b', sentence.lower())
    score = sum(2 for w in words if w in LEGAL_WORDS)
    if re.search(r'\d', sentence):
        score += 1
    if re.search(r'[$₹€£]\s?\d|\b\d+(?:\.\d+)?\s?%', sentence, re.I):
        score += 2
    if re.search(r'\b(shall|must|required|may|will|cannot|prohibited)\b', sentence, re.I):
        score += 2
    if re.search(r'\b(if|unless|provided that|subject to|in the event)\b', sentence, re.I):
        score += 1.5
    score += min(len(words) / 40, 1)
    if total > 1:
        score += (1 - index / (total - 1)) * 0.25
    return score

def summarize_text(text, max_sentences=5):
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return ' '.join(sentences)
    scored = [
        (sentence_score(s, i, len(sentences)), i, s)
        for i, s in enumerate(sentences)
    ]
    chosen = sorted(
        sorted(scored, reverse=True)[:max_sentences],
        key=lambda x: x[1]
    )
    return ' '.join(x[2] for x in chosen)

def summarize_with_metadata(text, max_sentences=5):
    sentences = split_sentences(text)
    summary = summarize_text(text, max_sentences)
    return {
        'original_sentence_count': len(sentences),
        'summary_sentence_count': len(split_sentences(summary)),
        'summary': summary
    }
