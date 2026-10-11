"""Build the catalog: contemporary romance novels from Hardcover, sorted onto shelves.

Hardcover's "Romance" genre includes Fourth Wing and The Fault in Our Stars, so a
book has to earn its place: readers must call it a romance, set in our world, today.
Each book then goes on one shelf (rom-com, heartfelt, romantic suspense or dark
romance), so the project can ask what separates a rom-com from a dark romance.
"""
import json
import re

from . import hardcover

FIELDS = """id slug title release_year pages rating ratings_count users_count
            description cached_tags image { url } contributions(limit: 1) { author { name } }"""

PULL = """query($offset: Int!) {
  books(where: {cached_tags: {_contains: {Genre: [{tag: "Romance"}]}},
                release_year: {_gte: 2000}, users_count: {_gte: 50}},
        order_by: {users_count: desc}, limit: 250, offset: $offset) { %s }
}""" % FIELDS

BY_TITLE = """query($title: String!) {
  books(where: {title: {_eq: $title}, ratings_count: {_gte: 50}},
        order_by: {users_count: desc}, limit: 1) { %s }
}""" % FIELDS

# The books this project started from. They're always in, even when a stray tag
# (a reader filing The Love Hypothesis under Young Adult) would have dropped them.
FAVORITES = ["The Unhoneymooners", "The Love Hypothesis", "You Deserve Each Other", "The Hating Game"]

# Readers tag loosely: Haunting Adeline gets three Fantasy votes, Twisted Love one
# Young Adult. So a genre only counts against a book when it gets at least half as
# many votes as Romance does.
OTHER_WORLD = {
    "Fantasy", "Science Fiction", "Dystopian", "Magic", "Historical Fiction", "Historical",
    "History", "War",
    "Romantasy", "Fantasy romance", "Paranormal", "Paranormal Romance", "Historical Romance",
    "Graphic Novels", "Comics", "Manga", "Middle Grade", "Children's",
}
YOUNG_ADULT = {"Young Adult", "Teen & Young Adult", "Juvenile Fiction", "Young Adult Fiction"}
NONFICTION = {"Nonfiction", "Non-fiction", "Self Help", "Self-help", "Psychology", "Memoir",
              "Biography", "Poetry", "Essays", "Relationships"}
ROMANCE = {"Romance", "Dark Romance", "Contemporary Romance"}
# Shelf labels that say nothing about what kind of book it is.
GENERIC = {"Fiction", "General", "Contemporary", "Literature & Fiction", "Adult", "Novel",
           "to-read", "physical-tbr", "did-not-finish", "Audiobook", "Spanish", "English"}
# Quality: widely read, well rated, and not erotica. Small self-published filler and
# books sold on explicit covers don't make it in.
MIN_READERS = 100
MIN_RATING = 3.6
EROTICA = {"erotica", "Erotica", "Erotic Romance", "Erotic romance", "Erotic fiction", "Erotic literature",
           "Erotic stories", "Erotic", "Spicy", "smut", "Smutty", "bdsm", "Dark Romance/Kink",
           "Fiction / Romance / Erotic"}
# Spice. Readers rarely tag it, and one "sexy" vote on Get a Life, Chloe Brown looks
# the same as one on a dark romance, so there are two levels:
#   hard: unmistakable (kink, BDSM, spice 4-5, "explicit content" in the blurb). Cut.
#   soft: a "steamy" or "spicy" vote, or "steamy" in the blurb. Kept, but flagged for
#         Suhani to approve or reject by author.
HARD_SPICE = re.compile(
    r"^(erotica|erotic.*|smut|smutty|bdsm|kink.*|spice[- ]?[45]|spice level [45]|spice [45]/5|"
    r"very explicit|explicit sexual content|sexual content/explicit scenes)$", re.I)
SOFT_SPICE = re.compile(r"^(steamy|sexy|spicy|dirty|high heat|taboo|open-door spice|spice[- ]?3|spice 3/5)$", re.I)
HARD_BLURB = re.compile(r"explicit (content|scenes|sex)|mature (readers|audiences|content)|\b18\+|erotic", re.I)
SOFT_BLURB = re.compile(r"steamy|scorching|filthy|dirty (talk|office|little)|kinky|\btaboo\b", re.I)

# Literary fiction with a love story inside it.
LITERARY = {"Literary Fiction", "Literary", "Literature"}

SUSPENSE = {"Thriller", "Mystery", "Suspense", "Romantic Suspense", "Psychological Thriller", "Crime"}

SHELVES = {
    "romcom": "Rom-com",
    "heartfelt": "Heartfelt",
    "suspense": "Romantic suspense",
    "dark": "Dark romance",
}


# Scope: the catalog covers M/F romance. Keyed by Hardcover id, because titles
# repeat (there are two books called The Long Game).
NOT_MF = {
    381772: "Red, White & Royal Blue",
    524964: "Heated Rivalry",
    524963: "Game Changer",
    552426: "The Long Game (Rachel Reid)",
    455105: "The Charm Offensive",
    790314: "Role Model",
    817516: "Pucking Around",
    817464: "God of Fury",
}

# Tags can't catch everything. These passed every rule and still aren't romance novels;
# each one is a judgment call, so each one says why.
NOT_ROMANCE = {
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
    "You": "a psychological thriller narrated by a stalker",
    "Serotonin": "literary fiction (Houellebecq)",
    "Fates and Furies": "literary fiction about a marriage",
    "Cleopatra and Frankenstein": "literary fiction about a marriage",
    "This is How You Lose Her": "a short story collection",
    "You Exist Too Much": "literary fiction",
    "How to Get Filthy Rich in Rising Asia": "literary fiction",
    "Ask Again, Yes": "a family saga",
    "Sing You Home": "a family drama",
    "Writers & Lovers": "literary fiction about a writer",
    "Savages": "a crime novel",
    "Naked Heat": "a mystery (a TV tie-in)",
    "The Giver of Stars": "historical fiction (1930s Kentucky)",
    "The Lady's Guide to Celestial Mechanics": "historical romance (Regency)",
    "Love in the Afternoon": "historical romance (Victorian)",
}


def tags(book, kind, top=5):
    return [t["tag"] for t in (book.get("cached_tags") or {}).get(kind, [])[:top]]


def votes(book, names):
    """The most readers who gave this book any one of these genres."""
    genres = (book.get("cached_tags") or {}).get("Genre", [])
    return max([t["count"] for t in genres if t["tag"] in names], default=0)


def why_not(book):
    """Return why a book isn't a contemporary romance, or None if it is."""
    if book["id"] in NOT_MF:
        return "outside scope: not M/F"
    if book["title"] in NOT_ROMANCE:
        return "hand-checked: " + NOT_ROMANCE[book["title"]]
    romance = votes(book, ROMANCE)
    top = max([t["count"] for t in book["cached_tags"].get("Genre", []) if t["tag"] not in GENERIC], default=0)
    if romance < 1 or romance < 0.75 * top:
        return "romance isn't the point"
    if votes(book, OTHER_WORLD) >= romance / 2:
        return "other world or era"
    if votes(book, YOUNG_ADULT) >= romance / 2:
        return "young adult"
    if votes(book, NONFICTION) >= romance / 2:
        return "nonfiction"
    if LITERARY & set(tags(book, "Genre")):
        return "literary fiction"
    if votes(book, EROTICA) * 3 >= romance:
        return "erotica"
    if spice(book) == "hard":
        return "explicit"
    if book["users_count"] < MIN_READERS:
        return "not widely read"
    if (book["rating"] or 0) < MIN_RATING:
        return "rated below 3.6"
    return None


def spice(book):
    """'hard', 'soft' or None, from readers' tags, warnings and moods, and the blurb."""
    cached = book.get("cached_tags") or {}
    found = [t["tag"].strip('"') for kind in ("Tag", "Content Warning", "Mood") for t in cached.get(kind, [])]
    blurb = book.get("description") or ""
    if any(HARD_SPICE.match(t) for t in found) or HARD_BLURB.search(blurb):
        return "hard"
    if any(SOFT_SPICE.match(t) for t in found) or SOFT_BLURB.search(blurb):
        return "soft"
    return None


def shelf(book):
    """Which kind of romance this is, from what readers tagged it."""
    genres = set(tags(book, "Genre"))
    moods = [m.lower() for m in tags(book, "Mood", top=3)]
    if "Dark Romance" in genres:
        return "dark"
    if SUSPENSE & genres:
        return "suspense"
    if "dark" in moods:
        return "dark"
    if {"funny", "lighthearted"} & set(moods):
        return "romcom"
    return "heartfelt"


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
        "shelf": shelf(book),
        "spice_flag": spice(book) == "soft",
        "genres": tags(book, "Genre"),
        "moods": {t["tag"].lower(): t["count"] for t in book["cached_tags"].get("Mood", [])},
        "content_warnings": {t["tag"].lower(): t["count"] for t in book["cached_tags"].get("Content Warning", [])},
        "reader_tags": {t["tag"].lower(): t["count"] for t in book["cached_tags"].get("Tag", [])},
        "favorite": book["title"] in FAVORITES,
    }


def pull():
    books = {}
    offset = 0
    while True:
        page = hardcover.query(PULL, {"offset": offset})["books"]
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
