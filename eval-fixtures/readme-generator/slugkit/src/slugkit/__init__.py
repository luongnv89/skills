"""Turn any title into a clean URL slug."""

import re
import unicodedata

__all__ = ["slugify"]


def slugify(text, separator="-", max_length=None):
    """Return a lowercase ASCII slug for text.

    Accents are folded to ASCII, punctuation is dropped, and words are joined
    with separator. When max_length is set, the slug is cut to that length and
    a trailing separator is removed.
    """
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z0-9]+", folded.lower())
    slug = separator.join(words)
    if max_length is not None:
        slug = slug[:max_length].rstrip(separator)
    return slug
