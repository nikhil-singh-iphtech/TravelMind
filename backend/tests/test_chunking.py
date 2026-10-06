from app.core.chunking import chunk_text


def test_chunk_text_splits_long_text_into_overlapping_pieces():
    text = " ".join(f"word{i}" for i in range(400))

    chunks = chunk_text(text, chunk_size=150, overlap=30)

    assert len(chunks) > 1
    first_words = chunks[0].split()
    second_words = chunks[1].split()
    assert first_words[-1] in second_words[:30]


def test_chunk_text_handles_short_text_as_one_chunk():
    chunks = chunk_text("just a few words here", chunk_size=150, overlap=30)
    assert chunks == ["just a few words here"]


def test_chunk_text_handles_empty_text():
    assert chunk_text("", chunk_size=150, overlap=30) == []