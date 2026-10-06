"""Build the catalog: contemporary rom-com novels from Hardcover.

Hardcover's "Romance" genre includes Fourth Wing and The Fault in Our Stars, so a
book has to earn its place. Readers must call it a romance, and must call it funny
or lighthearted. Then the rules below remove what isn't a contemporary rom-com.
"""
import json

from . import hardcover

FIELDS = """id slug title release_year pages rating ratings_count users_count
            description cached_tags image { url } contributions(limit: 1) { author { name } }"""

PULL = """query($mood: String!, $offset: Int!) {
  books(where: {cached_tags: {_contains: {Genre: [{tag: "Romance"}], Mood: [{tag: $mood}]}},
                release_year: {_gte: 2010}, ratings_count: {_gte: 50}},
        order_by: {users_count: desc}, limit: 250, offset: $offset) { %s }
}""" % FIELDS

BY_TITLE = """query($title: String!) {
  books(where: {title: {_eq: $title}, ratings_count: {_gte: 50}},
        order_by: {users_count: desc}, limit: 1) { %s }
}""" % FIELDS

# The books this project started from. They're always in, even when a stray tag
# (a reader filing The Love Hypothesis under Young Adult) would have dropped them.
FAVORITES = ["The Unhoneymooners", "The Love Hypothesis", "You Deserve Each Other", "The Hating Game"]

# Another world, another century or another age group: not a contemporary rom-com.
NOT_CONTEMPORARY = {
    "Fantasy", "Romantasy", "Fantasy romance", "Science Fiction", "Paranormal",
    "Paranormal Romance", "Dystopian", "Horror", "Magic", "Historical Romance",
    "Historical Fiction", "Historical", "Mystery", "Thriller", "Middle Grade",
    "Children's", "Juvenile Fiction", "Graphic Novels", "Comics", "Manga",
}
# Funny and tagged Romance, but literary fiction with a love story inside it.
LITERARY = {"Literary Fiction", "Literary", "Literature"}
# Young Adult only counts if it's one of the first two genres readers chose.
TOP_TWO_ONLY = {"Young Adult", "Teen & Young Adult"}


# Tags can't catch everything. These passed every rule and still aren't rom-coms;
# each one is a judgment call, so each one says why.
NOT_ROMCOMS = {
    "Modern Romance": "nonfiction (Aziz Ansari on dating)",
    "Stay Sexy & Don't Get Murdered: The Definitive How-To Guide": "nonfiction (a podcast memoir)",
    "Everything I Know About Love: A Memoir": "nonfiction (memoir)",
    "Love Does: Discover a Secretly Incredible Life in an Ordinary World": "nonfiction (Christian living)",
    "Notorious Nineteen": "mystery (Stephanie Plum)",
    "The Storied Life of A. J. Fikry": "literary fiction about a bookseller",
    "How to Be Both": "literary fiction",
    "The Lover's Dictionary": "literary fiction, told as dictionary entries",
    "Detransition, Baby": "literary fiction about a family",
    "Erotic Stories for Punjabi Widows": "a comic novel about a writing class, not a couple",
    "The Authenticity Project": "an ensemble novel about strangers",
    "The Bookshop on the Corner": "women's fiction; the romance is a subplot",
    "Someone Else's Shoes": "women's fiction about two women",
    "Crazy Rich Asians": "ensemble satire of the ultra-rich",
    "Rich People Problems": "ensemble satire (Crazy Rich Asians, book 3)",
    "Nick and Charlie": "a young adult novella",
}


def tags(book, kind, top=5):
    return [t["tag"] for t in (book.get("cached_tags") or {}).get(kind, [])[:top]]


def why_not(book):
    """Return why a book isn't a contemporary rom-com, or None if it is."""
    if book["title"] in NOT_ROMCOMS:
        return "hand-checked: " + NOT_ROMCOMS[book["title"]]
    genres = tags(book, "Genre")
    moods = [m.lower() for m in tags(book, "Mood", top=3)]
    if NOT_CONTEMPORARY & set(genres):
        return "other world or era: " + ", ".join(sorted(NOT_CONTEMPORARY & set(genres)))
    if LITERARY & set(genres):
        return "literary fiction"
    if TOP_TWO_ONLY & set(genres[:2]):
        return "young adult"
    if "Romance" not in genres[:3]:
        return "romance isn't the point"
    if "dark" in moods:
        return "dark romance"
    if not {"funny", "lighthearted"} & set(moods):
        return "not funny or lighthearted"
    return None


def clean(book):
    author = book["contributions"][0]["author"]["name"] if book["contributions"] else ""
    return {
        "id": book["id"],
        "slug": book["slug"],
        "title": book["title"],
        "author": " ".join(author.split()),
        "year": book["release_year"],
        "pages": book["pages"],
        "rating": round(book["rating"], 3) if book["rating"] else None,
        "ratings": book["ratings_count"],
        "readers": book["users_count"],
        "description": (book["description"] or "").strip(),
        "cover": (book.get("image") or {}).get("url"),
        "genres": tags(book, "Genre"),
        "moods": {t["tag"].lower(): t["count"] for t in book["cached_tags"].get("Mood", [])},
        "reader_tags": {t["tag"].lower(): t["count"] for t in book["cached_tags"].get("Tag", [])},
        "favorite": book["title"] in FAVORITES,
    }


def pull():
    books = {}
    for mood in ("funny", "lighthearted"):
        offset = 0
        while True:
            page = hardcover.query(PULL, {"mood": mood, "offset": offset})["books"]
            for book in page:
                books[book["id"]] = book
            if len(page) < 250:
                break
            offset += 250
    for title in FAVORITES:
        for book in hardcover.query(BY_TITLE, {"title": title})["books"]:
            books[book["id"]] = book
    return list(books.values())


def build(path=hardcover.ROOT / "data" / "books.json"):
    pulled = pull()
    kept, dropped = [], {}
    for book in pulled:
        reason = why_not(book)
        if reason is None or book["title"] in FAVORITES:
            kept.append(clean(book))
        else:
            dropped[reason.split(":")[0]] = dropped.get(reason.split(":")[0], 0) + 1
    kept.sort(key=lambda b: -b["readers"])
    path.write_text(json.dumps(kept, indent=1, ensure_ascii=False))
    return pulled, kept, dropped
