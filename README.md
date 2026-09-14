# openbook-starter

Writes OpenBook documents into a repo (`openbook start`). Not the specification.

Spec: https://github.com/openbook-data-standards/openbook

Apache-2.0. Python 3.11+.

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
openbook start --id acme-feeds --name "Acme Feeds" --base-url https://example.invalid/acme-feeds --no-input
```

Optional translations kernel (private git until public PyPI):

```bash
uv pip install -e ".[translations]"
# or: pip install git+ssh://git@github.com/openbook-data-standards/openbook-translate.git
```
