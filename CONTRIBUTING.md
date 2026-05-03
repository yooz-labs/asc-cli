# Contributing to asc-cli

Thanks for considering a contribution. asc-cli is a generic developer utility for the Apple App Store Connect API; PRs that add commands, improve coverage, or fix bugs are welcome.

## Before you start

- **License agreement**: this repository is licensed under [Apache License 2.0](LICENSE.md). By contributing, you agree your contribution is provided under the same license. The ecosystem licensing strategy lives in [yooz-engine/LICENSING.md](https://github.com/yooz-labs/yooz-engine/blob/main/LICENSING.md).
- **DCO sign-off** (required): every commit must carry a `Signed-off-by:` trailer.

  ```bash
  git commit -s -m "feat: add new pricing command"
  ```

  The `-s` flag adds a line like `Signed-off-by: Your Name <you@example.com>` derived from `git config user.name` and `user.email`.

- **Discuss first** for non-trivial changes. Open an issue describing the problem and the proposed approach before writing a large patch.

## Workflow

1. **Open an issue** describing the bug or feature (skip for trivial fixes).
2. **Branch from `main`**: `git checkout -b feature/issue-N-short-description`.
3. **Make atomic commits** with concise messages (under 50 chars on the subject line, no AI attribution).
4. **Run tests**:

   ```bash
   uv run pytest -v
   ```

5. **Run lint**: `uv run ruff check . && uv run ruff format --check .` and `uv run mypy src/`.
6. **Open a PR** against `main`. Describe what changed, why, and how to test it. Reference the issue number with `Closes #N`.
7. **Address review findings**. Maintainers run an automated multi-agent review on every PR.
8. **Merge after CI green**.

## Commit style

- Subject: imperative, present tense, under 50 chars, optional `type(#issue):` prefix.
- Body: what + why, not how. The diff shows how.
- No emojis, no AI attribution.

## What not to commit

- Secrets (`.env`, `.p8` private keys, API keys, App Store Connect credentials).
- Personal Apple Developer account identifiers in test fixtures.
- Generated artefacts (`dist/`, `htmlcov/`, `.coverage`) — these are gitignored.

## Tests

- **Unit tests**: pytest under `tests/`. Run before pushing.
- **Simulation engine**: integration tests use a local API simulation (no live App Store Connect calls). New commands should ship with simulation routes.
- **No mocks of internal modules**. Test against the real CLI surface.

## Code style

- Python 3.10+, `ruff` for lint and format, `mypy` for types.
- Use `pathlib.Path`, not `os.path`.
- Don't add error handling for impossible scenarios. Trust your function contracts.

## Security

Found a vulnerability? See [`SECURITY.md`](SECURITY.md) — please don't open a public issue.

## Questions

Open an issue, or email **dev@yooz.info**.
