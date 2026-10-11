import json
from pathlib import Path

from formula.catalog import FAVORITES, shelf, why_not

BOOKS = Path(__file__).resolve().parent.parent / "data" / "books.json"


def book(title="A Book", genres=(("Romance", 6), ("Contemporary", 2)), moods=("funny", "emotional"),
         readers=1000, rating=4.0, id=1):
    return {"id": id, "title": title, "users_count": readers, "rating": rating, "cached_tags": {
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


def test_quality_bar():
    assert why_not(book(readers=60)) == "not widely read"
    assert why_not(book(rating=2.68)) == "rated below 3.6"
    assert why_not(book(genres=(("Romance", 6), ("erotica", 2)))) == "erotica"
    # One stray vote (The Hating Game has one) is not enough.
    assert why_not(book(genres=(("Romance", 6), ("erotica", 1)))) is None


def test_spice_is_cut_or_flagged():
    from formula.catalog import spice
    hard = book(); hard["cached_tags"]["Tag"] = [{"tag": "spice-5", "count": 1}]
    assert why_not(hard) == "explicit"
    soft = book(); soft["cached_tags"]["Mood"].append({"tag": "steamy", "count": 1})
    assert why_not(soft) is None and spice(soft) == "soft"
    assert spice({"cached_tags": {}, "description": "Contains explicit content."}) == "hard"


def test_scope_is_mf_romance():
    assert why_not(book(id=381772)) == "outside scope: not M/F"


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
    assert shelves["Verity"] == "suspense"
    assert shelves["Butcher & Blackbird"] == "dark"
