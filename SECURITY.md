# Security policy

## Supported versions

Security fixes are accepted for the current `main` branch.

## Reporting a vulnerability

Please report vulnerabilities privately using GitHub Security Advisories instead of opening a public issue. Do not include sportsbook account credentials, cookies, authorization headers, or private browser profile data in reports.

## Scope

Relevant issues include:

- Committed secrets or unsafe credential handling.
- Scraper behavior that leaks private headers, cookies, account data, or location data.
- Dependency vulnerabilities that affect runtime or development workflows.
- GitHub Actions permission or supply-chain risks.

## CI security controls

The repository is configured for dependency review, `pip-audit`, workflow scanning with `zizmor`, secret scanning with the open-source `gitleaks` CLI container, and OSSF Scorecard. These are open-source or GitHub-native controls and do not require adding paid CI services.
