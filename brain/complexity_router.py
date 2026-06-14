"""
Complexity Router — classifica la query in <5ms prima di chiamare MLX.
Pattern da OpenJarvis: assegna token budget per evitare latenza inutile.
"""

import re

# (pattern, tier)
_RULES = [
    # triviale
    (r"^(ciao|ok|grazie|sì|no|bene|capito|perfetto)[\.\!]?$", "trivial"),
    (r"(che ore|che giorno|data di oggi)", "trivial"),
    # semplice
    (r"(apri|avvia|chiudi|metti|suona)", "simple"),
    (r"^.{1,40}$", "simple"),
    # complesso
    (r"(analizza|confronta|spiega nel dettaglio|pro e contro)", "complex"),
    (r"(architettura|progetta|implementa|refactor)", "complex"),
    # molto complesso
    (r"(analizza (tutti|questi|ogni)|trova (tutte|tutti))", "very_complex"),
]

TOKEN_BUDGET = {
    "trivial":      512,
    "simple":      1024,
    "moderate":    4096,
    "complex":     8192,
    "very_complex": 16384,
}

THINKING_TIERS = {"complex", "very_complex"}


def classify(text: str) -> tuple[str, int, bool]:
    """
    Restituisce (tier, max_tokens, use_thinking).
    """
    t = text.strip().lower()

    tier = "moderate"
    for pattern, label in _RULES:
        if re.search(pattern, t, re.IGNORECASE):
            tier = label
            break

    # Query lunga → almeno moderate
    if len(t) > 200 and tier in ("trivial", "simple"):
        tier = "moderate"

    use_thinking = tier in THINKING_TIERS
    return tier, TOKEN_BUDGET[tier], use_thinking
