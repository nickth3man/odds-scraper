# CI and release design

This project uses GitHub Actions, uv, Ruff, pyright, ty, pytest, and pytest-cov.

## Workflows

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `CI` | Pull requests and pushes to `main` | Ruff, type checks, tests, coverage, dependency review, and dependency audit. |
| `Release` | `v*.*.*` tags or manual dispatch | Re-run release checks, build distributions, generate provenance attestations, and publish a GitHub release. |
| `Security` | Weekly, manual, and relevant PR changes | `pip-audit`, `zizmor`, `gitleaks`, and OSSF Scorecard. |
| `Compatibility` | Weekly and manual | Smoke-test Python 3.12 and 3.13 across Linux, macOS, and Windows. |
| `Pull request labels` | Pull request activity | Apply labels based on changed files. |

## Coverage policy

CI enforces `--cov-fail-under=80`. Update `pyproject.toml` so local defaults match CI:

```toml
[tool.coverage.report]
fail_under = 80
show_missing = true
```

## Browser automation

The CI workflows install Chromium when Playwright is present. Tests should default to offline fixtures and should not depend on live sportsbook pages, account state, geo-gating, or bot detection behavior.

## Permissions

Workflows use explicit permissions. Artifact upload jobs request `artifact-metadata: write`. Release jobs request `id-token: write` and `attestations: write` so provenance can be generated.

## Release process

1. Update `pyproject.toml` version.
2. Update the changelog or release notes as needed.
3. Tag the commit with `vX.Y.Z`.
4. Push the tag.

The release workflow verifies that the tag matches the project version before publishing.
