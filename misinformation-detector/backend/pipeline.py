from claim_verifier import verify_claim
from counter_message import generate_counter_message
from explanation_generator import generate_explanation
from whisper_module import normalize_claim_text


def run_pipeline(claim_text: str) -> dict:
    claim = normalize_claim_text(claim_text)
    if not claim:
        raise ValueError("Claim cannot be empty")

    verdict, confidence, sources = verify_claim(claim)
    explanation = generate_explanation(claim, verdict, confidence, sources)
    counter_message = generate_counter_message(claim, verdict, confidence)

    return {
        "claim": claim,
        "verdict": verdict,
        "confidence": confidence,
        "sources": sources,
        "explanation": explanation,
        "counter_message": counter_message,
    }
