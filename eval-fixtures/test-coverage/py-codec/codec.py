"""Run-length encoding and whitespace helpers."""


def rle_encode(text: str) -> list[tuple[str, int]]:
    """Encode text as (character, run length) pairs. rle_decode reverses it."""
    runs: list[tuple[str, int]] = []
    for ch in text:
        if runs and runs[-1][0] == ch:
            runs[-1] = (ch, runs[-1][1] + 1)
        else:
            runs.append((ch, 1))
    return runs


def rle_decode(runs: list[tuple[str, int]]) -> str:
    """Rebuild the text rle_encode encoded."""
    return "".join(ch * count for ch, count in runs)


def normalize_space(text: str) -> str:
    """Collapse each run of whitespace to one space and strip both ends."""
    return " ".join(text.split())
