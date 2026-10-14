"""A small client for the Hardcover GraphQL API.

Every response is cached under data/raw/, so re-running the pipeline costs no requests.
The free plan allows 60 requests a minute; we stay under one a second.
"""
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
URL = "https://api.hardcover.app/v1/graphql"
_last_call = 0.0


def token():
    env = ROOT / ".env"
    for line in env.read_text().splitlines() if env.exists() else []:
        if line.startswith("HARDCOVER_TOKEN="):
            value = line.split("=", 1)[1].strip()
            if value:
                return value
    raise SystemExit("No Hardcover token. Put HARDCOVER_TOKEN=... in .env (see README).")


def query(text, variables=None, cache=True):
    """Run one GraphQL query and return its data, reading from the cache when we can."""
    global _last_call
    body = json.dumps({"query": text, "variables": variables or {}}, sort_keys=True)
    path = RAW / (hashlib.sha1(body.encode()).hexdigest()[:16] + ".json")
    if cache and path.exists():
        return json.loads(path.read_text())

    for attempt in range(4):
        wait = 1.1 - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()
        request = urllib.request.Request(URL, data=body.encode(), headers={
            "content-type": "application/json",
            "authorization": "Bearer " + token(),
            "user-agent": "romcom-formula (github.com/suhxnitiwari)",
        })
        try:
            reply = json.load(urllib.request.urlopen(request, timeout=60))
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise
        if "errors" in reply:
            raise RuntimeError(reply["errors"])
        RAW.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(reply["data"]))
        return reply["data"]
