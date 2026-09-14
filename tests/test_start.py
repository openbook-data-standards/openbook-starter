import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from openbook_starter.cli import WORKFLOW, main

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
EXAMPLE = Path(__file__).resolve().parent.parent / "openbook"


def _registry():
    schemas = {p.name: json.loads(p.read_text()) for p in SCHEMA_DIR.glob("*.json")}
    registry = Registry()
    for name, s in schemas.items():
        res = Resource(contents=s, specification=DRAFT202012)
        registry = registry.with_resource(name, res)
        if "$id" in s:
            registry = registry.with_resource(s["$id"], res)
    return schemas, registry


SCHEMAS, REGISTRY = _registry()
FORMAT = FormatChecker()


def _validate(doc: dict, stem: str) -> None:
    name = f"{stem}.schema.json"
    v = Draft202012Validator(SCHEMAS[name], registry=REGISTRY, format_checker=FORMAT)
    errors = [e.message for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path))]
    assert not errors, errors


def _start(tmp_path: Path, extra: list[str] | None = None) -> int:
    argv = [
        "start",
        "--id", "acme-feeds",
        "--name", "Acme Feeds",
        "--currency", "GBP",
        "--base-url", "https://example.invalid/acme-feeds",
        "--dir", str(tmp_path),
        "--no-input",
    ]
    if extra:
        argv.extend(extra)
    return main(argv)


def test_start_no_input(tmp_path: Path):
    assert _start(tmp_path) == 0
    pub = json.loads((tmp_path / "openbook" / "publisher.json").read_text())
    disc = json.loads((tmp_path / "openbook" / "discovery.json").read_text())
    snap = json.loads((tmp_path / "openbook" / "snapshot.json").read_text())
    assert pub["id"] == "acme-feeds"
    assert pub["sources"][0]["id"] == "acme-feeds-book"
    assert pub["sources"][0]["name"] == "Acme Feeds"
    assert pub["sources"][0]["sourceType"] == "sportsbook"
    assert len(pub["sources"]) == 1
    assert len(disc["feeds"]) == 1
    assert disc["feeds"][0]["kind"] == "snapshot"
    assert disc["feeds"][0]["url"] == "https://example.invalid/acme-feeds/snapshot.json"
    assert snap == pub
    assert (tmp_path / "openbook" / "README.md").is_file()
    wf = tmp_path / ".github" / "workflows" / "openbook-update.yml"
    assert wf.is_file()
    assert wf.read_text() == WORKFLOW
    _validate(pub, "publisher")
    _validate(disc, "discovery")
    _validate(snap, "publisher")


def test_refuses_without_force(tmp_path: Path):
    assert _start(tmp_path) == 0
    with pytest.raises(SystemExit, match="exists"):
        _start(tmp_path)


def test_force_overwrites(tmp_path: Path):
    assert _start(tmp_path) == 0
    (tmp_path / "openbook" / "publisher.json").write_text("{}\n")
    assert _start(tmp_path, ["--force"]) == 0
    pub = json.loads((tmp_path / "openbook" / "publisher.json").read_text())
    assert pub["id"] == "acme-feeds"
    _validate(pub, "publisher")


def test_no_workflow(tmp_path: Path):
    assert _start(tmp_path, ["--no-workflow"]) == 0
    assert not (tmp_path / ".github" / "workflows" / "openbook-update.yml").exists()
    _validate(json.loads((tmp_path / "openbook" / "publisher.json").read_text()), "publisher")


def test_skips_existing_workflow_without_force(tmp_path: Path, capsys):
    wf = tmp_path / ".github" / "workflows" / "openbook-update.yml"
    wf.parent.mkdir(parents=True)
    wf.write_text("keep\n")
    assert _start(tmp_path) == 0
    assert wf.read_text() == "keep\n"
    err = capsys.readouterr().err
    assert "skip existing" in err


def test_missing_id_no_input(tmp_path: Path):
    with pytest.raises(SystemExit, match="missing --id"):
        main(["start", "--dir", str(tmp_path), "--no-input"])


def test_invalid_id(tmp_path: Path):
    with pytest.raises(SystemExit, match="publisher id"):
        main([
            "start",
            "--id", "Acme",
            "--dir", str(tmp_path),
            "--no-input",
        ])


def test_invalid_currency(tmp_path: Path):
    with pytest.raises(SystemExit, match="ISO 4217"):
        main([
            "start",
            "--id", "acme-feeds",
            "--currency", "gbp",
            "--dir", str(tmp_path),
            "--no-input",
        ])


def test_defaults_without_name_or_base_url(tmp_path: Path):
    rc = main([
        "start",
        "--id", "acme-feeds",
        "--dir", str(tmp_path),
        "--no-input",
    ])
    assert rc == 0
    pub = json.loads((tmp_path / "openbook" / "publisher.json").read_text())
    assert pub["name"] == "acme-feeds"
    assert pub["baseCurrency"] == "GBP"
    assert pub["url"] == "https://example.invalid/acme-feeds"
    assert pub["sources"][0]["id"] == "acme-feeds-book"
    _validate(pub, "publisher")


def test_committed_example_matches_schemas():
    pub = json.loads((EXAMPLE / "publisher.json").read_text())
    disc = json.loads((EXAMPLE / "discovery.json").read_text())
    snap = json.loads((EXAMPLE / "snapshot.json").read_text())
    assert snap == pub
    assert pub["sources"][0]["id"] == "acme-feeds-book"
    assert len(disc["feeds"]) == 1
    _validate(pub, "publisher")
    _validate(disc, "discovery")
