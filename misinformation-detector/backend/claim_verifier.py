from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

HEADERS = {"User-Agent": "Mozilla/5.0"}
_MODEL = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def search_web(query: str, max_results: int = 6) -> List[str]:
    urls: List[str] = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                href = item.get("href")
                if href:
                    urls.append(href)
    except Exception:
        return []
    return urls


def extract_text(url: str, max_chars: int = 4000) -> str:
    try:
        response = requests.get(url, headers=HEADERS, timeout=6)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        return soup.get_text(" ", strip=True)[:max_chars]
    except Exception:
        return ""


def verify_claim(claim: str) -> Tuple[str, int, List[str]]:
    """
    Returns verdict, confidence percentage, and sources.
    Verdict: LIKELY TRUE | LIKELY FALSE | UNCERTAIN
    """
    urls = search_web(claim)
    evidence_texts: List[str] = []

    for url in urls:
        text = extract_text(url)
        if text:
            evidence_texts.append(text)

    if not evidence_texts:
        return "UNCERTAIN", 0, urls

    model = _get_model()
    claim_embedding = model.encode([claim])

    scores = []
    for text in evidence_texts:
        text_embedding = model.encode([text])
        similarity = cosine_similarity(claim_embedding, text_embedding)[0][0]
        scores.append(float(similarity))

    best_score = max(scores)
    confidence = max(0, min(100, round(best_score * 100)))

    if best_score > 0.65:
        verdict = "LIKELY TRUE"
    elif best_score > 0.45:
        verdict = "UNCERTAIN"
    else:
        verdict = "LIKELY FALSE"

    return verdict, confidence, urls
