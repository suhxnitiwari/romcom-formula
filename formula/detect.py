"""The trope detector: which tropes does each book use?

Two kinds of evidence:
  1. Readers' own trope tags on Hardcover ("enemies to lovers", "grumpy x sunshine"...).
     Only about one book in ten has them, but when they're there, they're people who read it.
  2. The book's description. Each trope has phrases that signal it, strong ones
     ("only one bed") worth 2 and suggestive ones ("roommate") worth 1. A trope needs
     2 points to count, so one loose word is never enough.

Reader tags double as the answer key: evaluate() grades the description reader
against the books readers tagged, without peeking at those tags. Those books are
split in two. Phrases were tuned only by reading the "dev" half; the "test" half
was never read, so its score is the honest one.
"""
import json
import re

from .hardcover import ROOT
from .tropes import TROPES

BOOKS = ROOT / "data" / "books.json"
THRESHOLD = 2

# Reader tags that name a trope, in the spellings readers actually use.
READER_TAGS = {
    "enemies_to_lovers": ["enemies to lovers", "rivals to lovers", "cruel/bully"],
    "friends_to_lovers": ["friends to lovers"],
    "fake_dating": ["fake dating", "fake relationship"],
    "workplace": ["workplace romance", "workplace"],
    "second_chance": ["second chance"],
    "forced_proximity": ["forced proximity", "force proximity", "roommates"],
    "grumpy_sunshine": ["grumpy sunshine", "grumpy x sunshine"],
    "marriage_of_convenience": ["marriage of convenience", "marriage of convinience"],
    "forbidden": ["forbidden love", "age gap", "romance: brother's best friend", "best friend's sibling",
                  "sibling's best friend", "parent's best friend", "friend s brother"],
    "opposites_attract": ["opposites attract"],
    "slow_burn": ["slow burn"],
    "love_triangle": ["love triangle"],
    "morally_gray": ["morally grey mmc", "morally grey characters", "morally gray", "stalker"],
}

# (pattern, points). Patterns are matched against the lowercased description.
PHRASES = {
    "enemies_to_lovers": [
        (r"enemies[- ]to[- ]lovers|rivals[- ]to[- ]lovers", 3),
        (r"\b(arch[- ]?)?nemes(is|es)\b|sworn enem|mortal enem", 2),
        (r"\brival(s|ry)?\b", 2),
        (r"can'?t stand (each other|him|her)|hate(s|d)? each other|loathe|despise|hate him|hate her", 2),
        (r"\bfeud|bicker|at each other'?s throats|butt heads|sparring|\bspar\b", 1),
    ],
    "friends_to_lovers": [
        (r"friends[- ]to[- ]lovers|more than friends|friend ?zone|ruin(ing)? (our|their|the) friendship", 3),
        (r"best friends? (since|for (years|ever))|childhood (best )?friends?|lifelong friend|oldest friend", 2),
        (r"just friends|only friends|platonic", 2),
        (r"\bfriendship\b", 1),
    ],
    "fake_dating": [
        (r"fake (dat\w*|relationship|boyfriend|girlfriend|fianc\w*|engagement|date|marriage)", 3),
        (r"pretend(s|ed|ing)? to (be (his|her|their|my) (girlfriend|boyfriend|fianc\w*|wife|husband|date|partner)|date|be dating|be together|be engaged|be a couple)", 3),
        (r"convinc\w+ .{0,60}(is|are|they'?re|she'?s|he'?s) dating", 2),
        (r"\bfake (it|one)\b|for show|plus[- ]one|wedding date", 1),
    ],
    "workplace": [
        (r"workplace romance|office romance", 3),
        (r"co-?workers?|colleagues?|work(s|ing)? (together|side by side)|same (company|firm|office|hospital|team|show)", 2),
        (r"\b(her|his|new) boss\b|\bpromotion\b|competing for (the|a) (job|position|role|promotion)", 2),
        (r"\boffice\b|\bassistant\b|\bintern\b|\bco-?host|\bpartner at\b|\bfirm\b", 1),
    ],
    "second_chance": [
        (r"second chance", 3),
        (r"\bex-?(boyfriend|girlfriend|husband|wife|fianc\w*)\b|high school sweetheart|the one that got away|first love", 2),
        (r"broke (her|his|my) heart|reunit\w+|back (in|into) (her|his|my) life|years (ago|later|after)|walked away", 1),
    ],
    "wrong_time": [
        (r"wrong time|never the right time|timing (is|was|has) never", 3),
        (r"(every|each) summer|summer after summer|over the (years|next decade)|for (a )?decades?", 2),
        (r"\byears\b.{0,40}\b(apart|later)\b|missed (chance|connection)|someone else", 1),
    ],
    "forced_proximity": [
        (r"forced proximity|only one bed|one bed|snowed in|under one roof", 3),
        (r"\broom ?mates?\b|flat ?share|share (a|an|the) (house|apartment|room|cabin|flat|bed|suite|tent)|live together|living together|move in (with|together)", 2),
        (r"stuck (together|with)|trapped|stranded|road trip|honeymoon|next door|neighbou?r|\bcabin\b|cross-country", 1),
    ],
    "grumpy_sunshine": [
        (r"grumpy|ray of sunshine|grumpy[- ]sunshine", 3),
        (r"\bgrump\b|surly|brood(y|ing)|scowl\w*|gruff|curmudgeon", 2),
        (r"sunshine|bubbly|cheerful|optimis\w+|cynic\w*", 1),
    ],
    "marriage_of_convenience": [
        (r"marriage of convenience|contract marriage|marriage contract|arranged marriage|green card", 3),
        (r"(needs|need) (a )?(wife|husband)|marry (him|her|me|a stranger)|on paper|in name only|wake up married|married in vegas", 2),
        (r"\bprenup|inheritance|\bproposal\b", 1),
    ],
    "forbidden": [
        (r"forbidden|off[- ]limits|taboo", 3),
        (r"(brother|sister|dad|father|mom|mother)'?s best friend|best friend'?s (brother|sister|dad|father|mom)|boyfriend'?s (dad|father)|step-?(brother|sister|father)", 3),
        (r"age gap|\bguardian\b|\bprofessor\b|\bher student\b|his student|\bpriest\b|\bmy boss\b|shouldn'?t want|can'?t have", 2),
        (r"\brules?\b|secret relationship|keep (it|this|their relationship) (a )?secret", 1),
    ],
    "opposites_attract": [
        (r"opposites attract|polar opposites?|complete opposites?|couldn'?t be more different|nothing in common", 3),
        (r"different worlds|free[- ]spirit|uptight|straight-?laced|city girl|small-town (boy|man|cowboy)", 1),
    ],
    "slow_burn": [
        (r"slow[- ]burn", 3),
        (r"little by little|over the course of|slowly (falling|fall)", 1),
    ],
    "love_triangle": [
        (r"love triangle|torn between|choose between (two|them|the two)", 3),
        (r"two (men|brothers|guys|women)|both (brothers|men|of them)|\bhis brother\b|her brother'?s twin", 1),
    ],
    "morally_gray": [
        (r"morally (gray|grey)|anti-?hero|villain", 3),
        (r"\bmafia\b|\bmob\b|cartel|bratva|hit ?man|assassin|\bkiller\b|serial|stalk\w*|kidnap\w*|obsess\w*", 2),
        (r"ruthless|dangerous|\bmonster\b|possessive|criminal|\bdon\b|psycho\w*|revenge|\bown (her|me)\b", 1),
    ],
    "unreliable_narrator": [
        (r"unreliable narrator|what really happened|the truth about (what|that night)", 3),
        (r"manuscript|\bconfession\b|can'?t remember|amnesia|lies (she|he)'?s (told|telling)|\bliar\b", 2),
        (r"\blies\b|not what (it|she|he) seems|\btwist", 1),
    ],
    "house_of_secrets": [
        (r"family secrets?|dark secrets?|haunted|skeletons", 3),
        (r"\bmansion\b|\bestate\b|\bmanor\b|\bthe house\b|small town'?s? secrets?|buried", 2),
        (r"\bsecrets?\b|hidden|the past", 1),
    ],
}


def reader_tropes(book):
    tags = book.get("reader_tags") or {}
    return {trope for trope, names in READER_TAGS.items() if any(n in tags for n in names)}


def description_scores(text):
    """Points per trope from the description, and the phrases that earned them."""
    text = (text or "").lower()
    scores, evidence = {}, {}
    for trope, rules in PHRASES.items():
        for pattern, points in rules:
            found = re.search(pattern, text)
            if found:
                scores[trope] = scores.get(trope, 0) + points
                evidence.setdefault(trope, []).append(found.group(0))
    return scores, evidence


def detect(book):
    """The tropes a book uses: what readers tagged, plus what the description says."""
    scores, evidence = description_scores(book.get("description"))
    from_text = {t for t, s in scores.items() if s >= THRESHOLD}
    from_readers = reader_tropes(book)
    return {
        "tropes": sorted(from_text | from_readers, key=list(TROPES).index),
        "from_readers": sorted(from_readers),
        "evidence": {t: evidence[t] for t in from_text},
    }


def split(book):
    """A fixed, arbitrary split: the same book always lands in the same half."""
    return "test" if book["id"] % 2 else "dev"


def evaluate(books, half=None):
    """Grade the description reader against books readers tagged.

    A book only counts for a trope if readers tagged at least one trope on it,
    so "no tag" means "readers didn't see it", not "nobody looked".
    """
    tagged = [b for b in books if reader_tropes(b) and (half is None or split(b) == half)]
    report = {}
    for trope in READER_TAGS:
        tp = fp = fn = 0
        for b in tagged:
            scores, _ = description_scores(b.get("description"))
            said, truth = scores.get(trope, 0) >= THRESHOLD, trope in reader_tropes(b)
            tp += said and truth
            fp += said and not truth
            fn += truth and not said
        if tp + fn:
            report[trope] = {
                "tagged": tp + fn,
                "found": tp,
                "recall": tp / (tp + fn),
                "precision": tp / (tp + fp) if tp + fp else None,
            }
    return len(tagged), report


def build():
    books = json.loads(BOOKS.read_text())
    for b in books:
        b.update(detect(b))
    BOOKS.write_text(json.dumps(books, indent=1, ensure_ascii=False))
    return books
