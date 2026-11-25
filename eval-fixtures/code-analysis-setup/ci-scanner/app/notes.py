def add_note(notes: list[str], text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("note text is empty")
    return [*notes, cleaned]
