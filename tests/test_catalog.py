import json
from pathlib import Path

from formula.catalog import FAVORITES, shelf, why_not

BOOKS = Path(__file__).resolve().parent.parent / "data" / "books.json"


def book(title="A Book", genres=(("Romance", 6), ("Contemporary", 2)), moods=("funny", "emotional")):
    return {"title": title, "cached_tags": {
        "Genre": [{"tag": g, "count": n} for g, n in genres], "Mood": [{"tag": m} for m in moods]}}


def test_a_contemporary_romance_is_in():
    assert why_not(book()) is None


def test_romance_has_to_be_what_readers_mostly_say():
    # The Tattooist of Auschwitz: one Romance vote, outnumbered.
    assert why_not(book(genres=(("War", 3), ("Romance", 1)))) == "romance isn't the point"
    # Verity: more Thriller than Romance votes, but close enough to count.
    assert why_not(book(genres=(("Thriller", 8), ("Romance", 6)))) is None
    # Generic shelf labels don't outvote anything.
    assert why_not(book(genres=(("Fiction", 9), ("Romance", 2)))) is None


def test_a_stray_tag_cant_drop_a_book():
    # Haunting Adeline: 3 Fantasy votes against 7 Romance.
    assert why_not(book(genres=(("Dark Romance", 7), ("Romance", 7), ("Fantasy", 3)))) is None
    # The Spanish Love Deception: 1 Young Adult vote against 3 Romance.
    assert why_not(book(genres=(("Romance", 3), ("Young Adult", 1)))) is None


def test_other_worlds_and_young_adult_are_out_when_readers_agree():
    assert why_not(book(genres=(("Romance", 4), ("Fantasy", 4)))) == "other world or era"
    assert why_not(book(genres=(("Romance", 3), ("Young Adult", 3)))) == "young adult"
    assert why_not(book(genres=(("Romance", 4), ("Literary Fiction", 1)))) == "literary fiction"
    assert why_not(book(title="Modern Romance")).startswith("hand-checked")


def test_shelves():
    assert shelf(book()) == "romcom"
    assert shelf(book(genres=(("Romance", 5), ("Dark Romance", 2)), moods=("funny",))) == "dark"
    assert shelf(book(genres=(("Romance", 5), ("Thriller", 2)), moods=("tense",))) == "suspense"
    assert shelf(book(moods=("dark", "tense"))) == "dark"
    assert shelf(book(moods=("emotional", "sad"))) == "heartfelt"


def test_the_catalog_keeps_the_books_this_started_from():
    if not BOOKS.exists():
        return  # the catalog is built from the API, so a fresh clone won't have it yet
    shelves = {b["title"]: b["shelf"] for b in json.loads(BOOKS.read_text())}
    assert set(FAVORITES) <= set(shelves)
    assert shelves["Birthday Girl"] and shelves["Haunting Adeline"] == "dark"
    assert shelves["Verity"] == "suspense"
