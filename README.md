# openbook-starter

Writes OpenBook documents into a repo (`openbook start`). Not the specification.

Spec: https://github.com/openbook-data-standards/openbook

Apache-2.0. Python 3.11+.

This repo is the CLI and a copyable example (`openbook/`). `start` writes documents only. It does not edit the caller’s pyproject. v1 is `start` only.

## Install

The repo is private. Until it is on PyPI:

```bash
pip install 'git+ssh://git@github.com/openbook-data-standards/openbook-starter.git'
```

From a checkout:

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

Optional translations kernel (separate repo; `start` does not install it for you):

```bash
pip install 'openbook-starter[translations]'
# while translate is private:
# pip install 'git+ssh://git@github.com/openbook-data-standards/openbook-translate.git'
```

## `openbook start`

Writes:

- `openbook/publisher.json`
- `openbook/discovery.json` — one feed, the snapshot URL that exists
- `openbook/snapshot.json` — the same document as `publisher.json`
- `openbook/README.md` — does not overwrite a root README
- `.github/workflows/openbook-update.yml` — unless `--no-workflow`

If `openbook/` already has files, the command refuses unless `--force`.

Flags; prompt only when a value is missing. `--no-input` is for scripts.

```bash
openbook start \
  --id acme-feeds \
  --name "Acme Feeds" \
  --currency GBP \
  --base-url https://example.invalid/acme-feeds \
  --no-input
```

| Flag | Meaning |
| --- | --- |
| `--id` | Publisher id (`^[a-z0-9][a-z0-9-]*$`) |
| `--name` | Display name (default: `--id`) |
| `--currency` | ISO 4217 alpha (default: `GBP`) |
| `--base-url` | Public base URL. Snapshot URL is `{base}/snapshot.json` |
| `--source-id` | Default `{id}-book` |
| `--source-name` | Default `--name` |
| `--dir` | Repo root (default: cwd) |
| `--no-input` | Do not prompt; exit if a required flag is missing |
| `--force` | Overwrite an existing `openbook/` |
| `--no-workflow` | Do not write the update workflow |

One source: `{publisher-id}-book`, name = publisher name. Discovery lists only that snapshot.

`openbookVersion` is `0.3.0-draft`.

## Update workflow

`openbook-update.yml` runs on a daily cron and `workflow_dispatch`. It compares `openbook/publisher.json` `openbookVersion` to the public spec `common.schema.json`. If the local version is gone from the spec, the job fails (CI red). It does not commit.

## Example

`openbook/` in this repo is `openbook start` output for Acme Feeds.
