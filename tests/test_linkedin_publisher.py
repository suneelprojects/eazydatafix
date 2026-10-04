"""Behavioral checks for daily LinkedIn delivery and duplicate prevention."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import linkedin_publisher as publisher


@pytest.fixture
def files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the publisher at an isolated editorial queue and ledger."""
    queue = tmp_path / "posts.json"
    ledger = tmp_path / "ledger.json"
    queue.write_text(json.dumps({"posts": [{"id": "post-one", "text": "Verified caption"}]}))
    ledger.write_text('{"entries": []}')
    monkeypatch.setattr(publisher, "QUEUE", queue)
    monkeypatch.setattr(publisher, "LEDGER", ledger)
    monkeypatch.setattr(publisher, "india_date", lambda: "2026-10-04")
    monkeypatch.setenv("LINKEDIN_ENABLED", "true")
    monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("LINKEDIN_PERSON_URN", "urn:li:person:test123")
    return ledger


def test_reservation_blocks_duplicate_and_uncertain_retry(files: Path) -> None:
    """Once reserved, another run must stop before another API call."""
    publisher.reserve()
    assert json.loads(files.read_text())["entries"][0]["status"] == "reserved"
    with pytest.raises(RuntimeError, match="earlier post remains reserved"):
        publisher.reserve()


def test_success_records_linkedin_id_and_skips_same_day(files: Path) -> None:
    """Record the returned ID and skip a second run for the same date."""
    publisher.reserve()

    class Response:
        status = 201
        headers = {"X-RestLi-Id": "urn:li:ugcPost:123"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with patch.object(publisher, "urlopen", return_value=Response()) as send:
        publisher.publish()
        body = json.loads(send.call_args.args[0].data)
        assert body["author"] == "urn:li:person:test123"
        share = body["specificContent"]["com.linkedin.ugc.ShareContent"]
        assert share["shareMediaCategory"] == "NONE"
    publisher.reserve()
    history = json.loads(files.read_text())["entries"]
    assert len(history) == 1
    assert history[0]["post_id"] == "urn:li:ugcPost:123"


def test_exhausted_queue_fails_closed(files: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No caption should silently repeat when the queue ends."""
    monkeypatch.setattr(publisher, "india_date", lambda: "2026-10-05")
    files.write_text(
        json.dumps(
            {"entries": [{"date": "2026-10-04", "id": "post-one", "status": "published"}]}
        )
    )
    with pytest.raises(RuntimeError, match="queue exhausted"):
        publisher.reserve()
