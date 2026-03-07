import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# -----------------------------
# Configuration
# -----------------------------

headers = {
    "User-Agent": "Mozilla/5.0"
}

# AI semantic similarity model
model = SentenceTransformer("all-MiniLM-L6-v2")


# -----------------------------
# Search Internet
# -----------------------------

def search_web(query):

    urls = []

    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=6)

        for r in results:
            urls.append(r["href"])

    return urls


# -----------------------------
# Extract Text From Webpages
# -----------------------------

def extract_text(url):

    try:
        response = requests.get(url, headers=headers, timeout=6)

        soup = BeautifulSoup(response.text, "lxml")

        text = soup.get_text()

        return text[:4000]

    except:
        return ""


# -----------------------------
# Verify Claim
# -----------------------------

def verify_claim(claim):

    urls = search_web(claim)

    evidence_texts = []

    for url in urls:

        text = extract_text(url)

        if text:
            evidence_texts.append(text)

    if not evidence_texts:
        return "UNCERTAIN", urls, 0

    claim_embedding = model.encode([claim])

    scores = []

    for text in evidence_texts:

        text_embedding = model.encode([text])

        similarity = cosine_similarity(
            claim_embedding,
            text_embedding
        )[0][0]

        scores.append(similarity)

    best_score = max(scores)

    if best_score > 0.65:
        verdict = "LIKELY TRUE"

    elif best_score > 0.45:
        verdict = "UNCERTAIN"

    else:
        verdict = "LIKELY FALSE"

    return verdict, urls, best_score


# -----------------------------
# AI Explanation Generator
# -----------------------------

def generate_explanation(claim, verdict):

    if verdict == "LIKELY FALSE":

        return f"The claim '{claim}' is likely misinformation. Reliable online sources do not support this statement."

    elif verdict == "LIKELY TRUE":

        return f"The claim '{claim}' appears to be supported by several online sources."

    else:

        return f"The claim '{claim}' could not be clearly verified because available information is limited or conflicting."


# -----------------------------
# Counter Message Generator
# -----------------------------

def generate_counter_message(claim, verdict):

    if verdict == "LIKELY FALSE":

        return f"""⚠️ Fact Check Alert

The claim:
"{claim}"

appears to be FALSE.

Please verify information before sharing and rely on trusted sources such as WHO, government health agencies, or medical professionals.
"""

    elif verdict == "LIKELY TRUE":

        return f"""✅ Fact Check

The claim:
"{claim}"

appears to be supported by reliable sources.
"""

    else:

        return f"""⚠️ Fact Check Notice

The claim:
"{claim}"

could not be fully verified.

Please check trusted sources before sharing.
"""


# -----------------------------
# Main Program
# -----------------------------

claim = input("Enter claim: ")

verdict, sources, score = verify_claim(claim)

confidence = round(score * 100)


print("\n---------------------------------")
print("Claim:")
print(claim)

print("\nVerdict:")

if verdict == "LIKELY TRUE":
    print("✅ Likely True")

elif verdict == "LIKELY FALSE":
    print("❌ Likely False")

else:
    print("⚠️ Uncertain")


print("\nConfidence:")
print(f"{confidence}%")


print("\nSources Checked:")

for s in sources[:3]:
    print("•", s)


print("\nExplanation:")
print(generate_explanation(claim, verdict))


print("\nCounter Message:")
print(generate_counter_message(claim, verdict))


print("---------------------------------")