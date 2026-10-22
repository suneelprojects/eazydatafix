"""Publish one curated EazyDataFix LinkedIn post per India-local day.

The ledger is committed before the network request. A failed or ambiguous request
remains reserved so a rerun cannot accidentally publish a second post.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "linkedin_posts.json"
LEDGER = BASE / "linkedin_published.json"
INDIA = ZoneInfo("Asia/Kolkata")
API = "https://api.linkedin.com/v2/ugcPosts"


def read_json(path: Path) -> dict:
    """Load an object from a JSON file."""
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return result


def write_json(path: Path, value: dict) -> None:
    """Write deterministic, readable JSON."""
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def posts() -> list[dict]:
    """Return validated, ordered posts from the editorial queue."""
    items = read_json(QUEUE).get("posts")
    if not isinstance(items, list):
        raise ValueError("posts must be a list")
    ids = set()
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise ValueError("Each post needs a string id")
        if not re.fullmatch(r"[a-z0-9-]+", item["id"]) or item["id"] in ids:
            raise ValueError(f"Duplicate or invalid post id: {item['id']}")
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError(f"Empty post: {item['id']}")
        if len(item["text"]) > 3000:
            raise ValueError(f"Post exceeds 3000 characters: {item['id']}")
        ids.add(item["id"])
    return items


def entries() -> list[dict]:
    """Load the persistent delivery ledger."""
    value = read_json(LEDGER).get("entries")
    if not isinstance(value, list):
        raise ValueError("entries must be a list")
    return value


def india_date() -> str:
    """Return today's date in the account's posting timezone."""
    return datetime.now(INDIA).date().isoformat()


def next_post(items: list[dict], history: list[dict]) -> dict | None:
    """Pick the first post that has never been reserved."""
    used = {row["id"] for row in history}
    return next((item for item in items if item["id"] not in used), None)


def preview() -> None:
    """Show the next caption without needing credentials or changing state."""
    item = next_post(posts(), entries())
    if item is None:
        raise RuntimeError("Editorial queue exhausted. Add a new verified post before publishing.")
    print(f"Next post: {item['id']} ({india_date()})\n\n{item['text']}")


def reserve() -> None:
    """Reserve a day and post before making an irreversible API request."""
    if os.environ.get("LINKEDIN_ENABLED") != "true":
        raise RuntimeError("Publishing is disabled. Set repository variable LINKEDIN_ENABLED=true.")
    if not os.environ.get("LINKEDIN_ACCESS_TOKEN"):
        raise RuntimeError("Missing LINKEDIN_ACCESS_TOKEN secret")
    if not re.fullmatch(r"urn:li:person:[A-Za-z0-9_-]+", os.environ.get("LINKEDIN_PERSON_URN", "")):
        raise RuntimeError("Missing or invalid LINKEDIN_PERSON_URN secret")
    history = entries()
    if any(row["status"] == "reserved" for row in history):
        raise RuntimeError(
            "An earlier post remains reserved. Reconcile it on LinkedIn before retrying."
        )
    if any(row["date"] == india_date() for row in history):
        print("One post is already recorded for today; skipping.")
        return
    item = next_post(posts(), history)
    if item is None:
        raise RuntimeError("Editorial queue exhausted. Add a new verified post before publishing.")
    history.append({"date": india_date(), "id": item["id"], "status": "reserved"})
    write_json(LEDGER, {"entries": history})
    print(f"Reserved {item['id']} for {india_date()}")


def payload(author: str, text: str) -> dict:
    """Build the official member text-share request body."""
    return {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }


def publish() -> None:
    """Submit the reserved post once and record its LinkedIn ID."""
    history = entries()
    reserved = [row for row in history if row["status"] == "reserved"]
    if len(reserved) != 1 or reserved[0]["date"] != india_date():
        raise RuntimeError("Expected exactly one reservation for today's India-local date")
    row = reserved[0]
    item = next(post for post in posts() if post["id"] == row["id"])
    token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    author = os.environ["LINKEDIN_PERSON_URN"]
    request = Request(
        API,
        data=json.dumps(payload(author, item["text"])).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 201:
                raise RuntimeError(f"Unexpected LinkedIn status: {response.status}")
            post_id = response.headers.get("X-RestLi-Id")
    except HTTPError as error:
        # Do not log headers, response bodies, or credentials.
        raise RuntimeError(f"LinkedIn returned HTTP {error.code}; reservation retained") from None
    except URLError:
        raise RuntimeError("LinkedIn connection failed; reservation retained") from None
    if not post_id:
        raise RuntimeError("LinkedIn returned no post ID; reservation retained")
    row["status"] = "published"
    row["post_id"] = post_id
    write_json(LEDGER, {"entries": history})
    print(f"Published {row['id']}: {post_id}")


def main() -> None:
    """Run one phase of the daily publisher."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("preview", "reserve", "publish"))
    phase = parser.parse_args().phase
    try:
        {"preview": preview, "reserve": reserve, "publish": publish}[phase]()
    except (ValueError, RuntimeError, KeyError) as error:
        print(f"Publisher stopped: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
