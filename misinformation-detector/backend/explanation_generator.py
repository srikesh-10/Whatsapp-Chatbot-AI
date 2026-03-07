from typing import List


def generate_explanation(claim: str, verdict: str, confidence: int, sources: List[str]) -> str:
    source_hint = (
        f" {len(sources)} sources were checked."
        if sources
        else " No reliable sources could be extracted during this check."
    )

    if verdict == "LIKELY FALSE":
        return (
            f"The claim '{claim}' is likely misinformation with confidence {confidence}%."
            " Reliable evidence does not support it." + source_hint
        )

    if verdict == "LIKELY TRUE":
        return (
            f"The claim '{claim}' appears supported by available evidence with confidence {confidence}%."
            + source_hint
        )

    return (
        f"The claim '{claim}' is uncertain with confidence {confidence}% because available evidence is mixed"
        " or limited." + source_hint
    )
