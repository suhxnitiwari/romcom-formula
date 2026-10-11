# The Rom-Com Formula ✦

*What separates a rom-com from a dark romance?*

## Ownership

© 2026 Suhani Tiwari. **All rights reserved.** This is my original work. The code is public so you can see how I build, not so you can reuse it: copying, reusing or republishing any part of it, including for a portfolio or a class assignment, is not permitted without my written permission. See [LICENSE](LICENSE).

## What it is

Enemies to lovers, fake dating, one bed. Romance readers shop by trope, so I'm testing what tropes really explain: which ones mark a book as a rom-com or a dark romance, and whether they predict how much readers love it. That takes a trope detector that reads book descriptions, graded against books I tagged by hand, and a model of what predicts a book's rating.

It starts from four books I love: *The Unhoneymooners*, *The Love Hypothesis*, *You Deserve Each Other* and *The Hating Game*.

**Status:** catalog and tagging sheet are built; the trope detector and rating model are next.

## How it's built

1. **Catalog** (`formula/catalog.py`): pulls every romance on [Hardcover](https://hardcover.app) from 2010 on with 50+ ratings (1,536 books) and keeps the contemporary ones. Readers tag loosely, so the rules compare vote counts: a book stays if Romance is what readers mostly call it, and a stray Fantasy or Young Adult vote can't drop it. The few that slip through are removed by hand, each with its reason in the code. 410 books remain, each on a shelf: rom-com (263), heartfelt (59), romantic suspense (25) or dark romance (63).
2. **Codebook** (`formula/tropes.py`): fifteen tropes, each with a one-line definition an annotator can apply the same way every time.
3. **Ground truth** (`formula/label.py`, `web/label.html`): a local page where I tag the tropes in books I've read. Those labels (`data/labels.json`) are what the detector is graded against.

```bash
python3 -m formula catalog   # build data/books.json (needs a Hardcover API key)
python3 -m formula label     # open the tagging sheet
python3 -m pytest            # run the tests
```

## Data

Book data comes from the [Hardcover API](https://docs.hardcover.app). To rebuild it, create a free key at hardcover.app/account/api and put `HARDCOVER_TOKEN=...` in a `.env` file. The built catalog isn't committed, because the publisher descriptions in it aren't mine to republish. Trope definitions are my own, informed by Kindlepreneur's [Book Tropes by Genre](https://kindlepreneur.com/book-tropes/).
