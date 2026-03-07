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
            results = ddgs.text(query, max_results=max_results)
            for item in results:
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
        text = soup.get_text(" ", strip=True)
        return text[:max_chars]
    except Exception:
        return ""


def verify_claim(claim: str) -> Tuple[str, List[str], float]:
    urls = search_web(claim)
    evidence_texts: List[str] = []

    for url in urls:
        text = extract_text(url)
        if text:
            evidence_texts.append(text)

    if not evidence_texts:
        return "UNCERTAIN", urls, 0.0

    model = _get_model()
    claim_embedding = model.encode([claim])

    scores = []
    for text in evidence_texts:
        text_embedding = model.encode([text])
        similarity = cosine_similarity(claim_embedding, text_embedding)[0][0]
        scores.append(float(similarity))

    best_score = max(scores)

    if best_score > 0.65:
        verdict = "LIKELY TRUE"
    elif best_score > 0.45:
        verdict = "UNCERTAIN"
    else:
        verdict = "LIKELY FALSE"

    return verdict, urls, best_score


def generate_explanation(claim: str, verdict: str) -> str:
    if verdict == "LIKELY FALSE":
        return (
            f"The claim '{claim}' is likely misinformation. "
            "Reliable online sources do not support this statement."
        )
    if verdict == "LIKELY TRUE":
        return f"The claim '{claim}' appears to be supported by several online sources."
    return (
        f"The claim '{claim}' could not be clearly verified because available "
        "information is limited or conflicting."
    )


def generate_counter_message(claim: str, verdict: str) -> str:
    if verdict == "LIKELY FALSE":
        return (
            "FACT CHECK ALERT\n\n"
            f"The claim:\n\"{claim}\"\n\n"
            "appears to be FALSE.\n\n"
            "Please verify information before sharing and rely on trusted "
            "sources such as WHO, government health agencies, or medical professionals."
        )
    if verdict == "LIKELY TRUE":
        return (
            "FACT CHECK\n\n"
            f"The claim:\n\"{claim}\"\n\n"
            "appears to be supported by reliable sources."
        )
    return (
        "FACT CHECK NOTICE\n\n"
        f"The claim:\n\"{claim}\"\n\n"
        "could not be fully verified.\n\n"
        "Please check trusted sources before sharing."
    )


def format_factcheck_report(claim: str, verdict: str, sources: List[str], score: float) -> str:
    confidence = round(score * 100)
    top_sources = "\n".join(f"- {src}" for src in sources[:3]) if sources else "- No sources found"
    explanation = generate_explanation(claim, verdict)
    counter = generate_counter_message(claim, verdict)
    return (
        f"Claim: {claim}\n"
        f"Verdict: {verdict}\n"
        f"Confidence: {confidence}%\n"
        f"Sources:\n{top_sources}\n\n"
        f"Explanation: {explanation}\n\n"
        f"{counter}"
    )


def main() -> None:
    claim = input("Enter claim: ").strip()
    if not claim:
        print("No claim provided.")
        return

    verdict, sources, score = verify_claim(claim)
    report = format_factcheck_report(claim, verdict, sources, score)
    print("\n---------------------------------")
    print(report)
    print("---------------------------------")


if __name__ == "__main__":
    main()