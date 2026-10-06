import json
from pathlib import Path

from formula.catalog import FAVORITES, why_not

BOOKS = Path(__file__).resolve().parent.parent / "data" / "books.json"


def book(title="A Book", genres=("Romance", "Contemporary"), moods=("funny", "emotional")):
    return {"title": title, "cached_tags": {
        "Genre": [{"tag": g} for g in genres], "Mood": [{"tag": m} for m in moods]}}


def test_a_funny_contemporary_romance_is_in():
    assert why_not(book()) is None


def test_another_world_or_era_is_out():
    assert why_not(book(genres=("Romance", "Fantasy"))).startswith("other world")
    assert why_not(book(genres=("Romance", "Historical Romance"))).startswith("other world")


def test_young_adult_only_counts_near_the_top():
    assert why_not(book(genres=("Young Adult", "Romance"))) == "young adult"
    # One reader filing The Love Hypothesis under YA doesn't make it YA.
    assert why_not(book(genres=("Romance", "Contemporary", "Young Adult"))) is None


def test_it_has_to_be_a_romance_and_funny():
    assert why_not(book(genres=("Contemporary", "Friendship", "Humor", "Romance"))) == "romance isn't the point"
    assert why_not(book(moods=("sad", "reflective", "emotional"))) == "not funny or lighthearted"
    assert why_not(book(moods=("dark", "funny", "tense"))) == "dark romance"


def test_literary_fiction_and_hand_checked_books_are_out():
    assert why_not(book(genres=("Literary Fiction", "Romance"))) == "literary fiction"
    assert why_not(book(title="Modern Romance")).startswith("hand-checked")


def test_the_catalog_keeps_the_four_favorites():
    if not BOOKS.exists():
        return  # the catalog is built from the API, so a fresh clone won't have it yet
    titles = {b["title"] for b in json.loads(BOOKS.read_text())}
    assert set(FAVORITES) <= titles
    assert "Birthday Girl" in titles
