def generate_counter_message(claim: str, verdict: str, confidence: int) -> str:
    if verdict == "LIKELY FALSE":
        return (
            "FACT CHECK ALERT\n\n"
            f"The claim \"{claim}\" appears to be false ({confidence}% confidence).\n"
            "Please verify information before sharing."
        )

    if verdict == "LIKELY TRUE":
        return (
            "FACT CHECK\n\n"
            f"The claim \"{claim}\" appears to be true ({confidence}% confidence)."
        )

    return (
        "FACT CHECK NOTICE\n\n"
        f"The claim \"{claim}\" could not be fully verified ({confidence}% confidence).\n"
        "Please consult trusted sources before sharing."
    )
