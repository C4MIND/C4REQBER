"""License compliance checker for C4REQBER."""


# BSD-style licenses (allowed for commercial use)
BSD_ALLOWED = {"lean4", "metarocq", "lean4lean"}

def check_commercial_use(source: str) -> bool:
    """Check if a third-party source is allowed for commercial use.

    Args:
        source: Name of the third-party source.

    Returns:
        bool: True if commercial use is allowed, False otherwise.
    """
    non_commercial_sources = {"Semantic Scholar"}
    if source in non_commercial_sources:
        print(f"WARNING: {source} is non-commercial only")
        return False

    proprietary_sources = {"ResearchGate", "SciMatic", "Grok (X.ai)"}
    if source in proprietary_sources:
        print(f"WARNING: {source} is proprietary — user must provide own API key")
        if source == "Grok (X.ai)":
            print(f"WARNING: PAID tier required (~$100/month) for {source}")
        return False

    # BSD-style licenses are allowed
    if source in BSD_ALLOWED:
        return True

    return True
