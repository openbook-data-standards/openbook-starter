from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PUB_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
SPEC = "0.3.0-draft"
WORKFLOW = """name: update
on:
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Spec version vs local documents
        run: |
          set -e
          LOCAL=$(python3 -c "import json; print(json.load(open('openbook/publisher.json'))['openbookVersion'])")
          curl -fsSL -o /tmp/common.schema.json \\
            https://raw.githubusercontent.com/openbook-data-standards/openbook/main/schema/common.schema.json
          if ! grep -q "$LOCAL" /tmp/common.schema.json; then
            echo "openbookVersion $LOCAL not found in latest spec common.schema.json"
            exit 1
          fi
"""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ask(args, key: str, prompt: str, default: str = "") -> str:
    val = getattr(args, key) or ""
    if val:
        return val
    if args.no_input:
        if default:
            return default
        sys.exit(f"missing --{key.replace('_', '-')} (and --no-input)")
    shown = f"{prompt} [{default}]: " if default else f"{prompt}: "
    got = input(shown).strip()
    return got or default


def publisher_doc(args) -> dict:
    stamp = _now()
    return {
        "openbookVersion": SPEC,
        "id": args.id,
        "sequence": 1,
        "dateModified": stamp,
        "name": args.name,
        "baseCurrency": args.currency,
        "url": args.base_url,
        "sources": [
            {
                "id": args.source_id,
                "name": args.source_name,
                "sourceType": "sportsbook",
            }
        ],
    }


def discovery_doc(args) -> dict:
    base = args.base_url.rstrip("/")
    return {
        "lastUpdated": _now(),
        "ttl": 60,
        "feeds": [
            {
                "name": "snapshot",
                "kind": "snapshot",
                "url": f"{base}/snapshot.json",
            }
        ],
    }


def readme(args) -> str:
    return (
        f"# {args.name} — OpenBook documents\n\n"
        f"Written by `openbook start`. Replace `{args.base_url}` with your host.\n"
        "Spec: https://github.com/openbook-data-standards/openbook\n"
    )


def start(args) -> int:
    args.id = _ask(args, "id", "Publisher id", "")
    if not PUB_ID.match(args.id):
        sys.exit("publisher id must match ^[a-z0-9][a-z0-9-]*$")
    args.name = _ask(args, "name", "Display name", args.id)
    args.currency = _ask(args, "currency", "ISO 4217 currency", "GBP")
    if not re.match(r"^[A-Z]{3}$", args.currency):
        sys.exit("currency must be ISO 4217 alpha")
    args.base_url = _ask(
        args, "base_url", "Public base URL", f"https://example.invalid/{args.id}"
    ).rstrip("/")
    args.source_id = args.source_id or f"{args.id}-book"
    args.source_name = args.source_name or args.name

    root = Path(args.dir).resolve()
    dest = root / "openbook"
    if dest.exists() and any(dest.iterdir()) and not args.force:
        sys.exit(f"{dest} exists (use --force)")
    dest.mkdir(parents=True, exist_ok=True)
    pub = publisher_doc(args)
    snap = json.loads(json.dumps(pub))
    (dest / "publisher.json").write_text(json.dumps(pub, indent=2) + "\n")
    (dest / "discovery.json").write_text(json.dumps(discovery_doc(args), indent=2) + "\n")
    (dest / "snapshot.json").write_text(json.dumps(snap, indent=2) + "\n")
    (dest / "README.md").write_text(readme(args))
    wf = root / ".github" / "workflows" / "openbook-update.yml"
    if args.workflow:
        if wf.exists() and not args.force:
            print(f"skip existing {wf}", file=sys.stderr)
        else:
            wf.parent.mkdir(parents=True, exist_ok=True)
            wf.write_text(WORKFLOW)
    print(f"wrote OpenBook documents in {dest}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="openbook")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("start", help="write openbook/ documents into a repo")
    sp.add_argument("--id", default="")
    sp.add_argument("--name", default="")
    sp.add_argument("--currency", default="")
    sp.add_argument("--base-url", default="", dest="base_url")
    sp.add_argument("--source-id", default="", dest="source_id")
    sp.add_argument("--source-name", default="", dest="source_name")
    sp.add_argument("--dir", default=".", help="repo root (default cwd)")
    sp.add_argument("--no-input", action="store_true")
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--no-workflow", dest="workflow", action="store_false")
    sp.set_defaults(workflow=True)
    args = p.parse_args(argv)
    if args.cmd == "start":
        return start(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
