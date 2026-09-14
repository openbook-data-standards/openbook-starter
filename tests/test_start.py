import pytest
from pathlib import Path

from openbook_starter.cli import main


def test_start_no_input(tmp_path: Path):
    rc = main([
        "start",
        "--id", "acme-feeds",
        "--name", "Acme Feeds",
        "--currency", "GBP",
        "--base-url", "https://example.invalid/acme-feeds",
        "--dir", str(tmp_path),
        "--no-input",
    ])
    assert rc == 0
    import json
    pub = json.loads((tmp_path / "openbook" / "publisher.json").read_text())
    disc = json.loads((tmp_path / "openbook" / "discovery.json").read_text())
    snap = json.loads((tmp_path / "openbook" / "snapshot.json").read_text())
    assert pub["id"] == "acme-feeds"
    assert pub["sources"][0]["id"] == "acme-feeds-book"
    assert len(disc["feeds"]) == 1
    assert disc["feeds"][0]["kind"] == "snapshot"
    assert snap["id"] == pub["id"]
    assert (tmp_path / "openbook" / "README.md").is_file()
    assert (tmp_path / ".github" / "workflows" / "openbook-update.yml").is_file()


def test_refuses_without_force(tmp_path: Path):
    assert main(["start", "--id", "acme-feeds", "--dir", str(tmp_path), "--no-input"]) == 0
    with pytest.raises(SystemExit):
        main(["start", "--id", "acme-feeds", "--dir", str(tmp_path), "--no-input"])
