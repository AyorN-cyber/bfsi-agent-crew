# Contributing

Thanks for taking a look. Small, focused pull requests are easiest to review.

## Setup

```bash
git clone https://github.com/AyorN-cyber/bfsi-agent-crew.git
cd bfsi-agent-crew
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Guidelines

- Add or update tests with every change. The suite runs offline and should stay fast.
- Keep numeric checks in `rules.py` and keep `data/policies/` in sync with them.
- Do not add real personal or financial data. Everything in this repository is synthetic.
- Agents may reason and write, but they should not recalculate verified numbers.

## Pull requests

Describe what changed and why, and mention how you tested it. For larger ideas, open an issue first so we can agree on the approach.
