def chunk_text(text: str, chunk_size: int = 150, overlap: int = 30) -> list[str]:
    """
    Splits text into overlapping windows of chunk_size words, each
    overlapping the previous by `overlap` words. Plain arithmetic on
    word counts — deterministic, same rule as BudgetCalculator: this
    doesn't need to be probabilistic.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap
    return chunks