# Contributing to Geneva

Thanks for your interest. Geneva is in active early development — contributions are welcome, especially in the areas below.

---

## Where contributions help most

- **Bug fixes** — especially in memory operations, provider adapters, or tool execution
- **Provider adapters** — adding support for new LLM providers under `src/providers/`
- **Test coverage** — extending `tests/` for edge cases in memory or research engine
- **Documentation** — improving setup guides, skill examples, or architecture diagrams
- **Skills** — sharing useful `.geneva/skills/` examples

Layer 1 (AI-to-AI collaboration protocol) is not yet open for external contribution — it is in private validation.

---

## Setup

```bash
git clone https://github.com/jintaphonteosuwan/geneva
cd geneva
pip install -e ".[dev]"
pytest                  # must pass before submitting
cd geneva-ui && npm install && npm run build
```

---

## Pull Request Guidelines

1. **Open an issue first** for anything non-trivial — alignment before code saves time
2. **One concern per PR** — bug fix, feature, or refactor; not all three
3. **Tests required** — new behaviour needs a test; `pytest` must pass at 0 failures
4. **No new dependencies** without discussion — Geneva's dependency footprint is intentional
5. **Commit style** — short imperative subject line (`fix: memory write race`, `feat: ollama provider`)

---

## Code Style

- Python: `ruff` for linting, no hard formatter enforced — match the surrounding style
- TypeScript: `prettier` via `npm run lint` in `geneva-ui/`
- No inline comments explaining *what* the code does — only *why* when non-obvious

---

## Reporting Bugs

Open a GitHub issue with:
- Geneva version (`geneva --version`)
- Provider and model
- Minimal reproduction steps
- Expected vs actual behaviour
