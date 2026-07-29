# Security Policy

EazyDataFix takes responsible vulnerability disclosure seriously. Please report
suspected security issues privately so maintainers can investigate them before
details are made public.

## Supported Versions

Security updates are currently considered for the latest stable release line.

| Release line | Security updates |
| --- | --- |
| 0.3.x | Supported |
| 0.2.x and earlier | Not supported |

This is not a long-term support commitment. Where possible, reproduce and report
a vulnerability against the latest EazyDataFix release.

## Reporting a Vulnerability

Do not open a public GitHub issue for a suspected vulnerability or disclose
sensitive details publicly.

To submit a confidential report:

1. Open the EazyDataFix repository's **Security** tab on GitHub.
2. Select **Report a vulnerability**.
3. Submit the report privately through GitHub Private Vulnerability Reporting.

Use the private report for all vulnerability details and follow-up discussion.

## Information to Include

Provide enough information to help maintainers understand and reproduce the
issue:

- A clear description of the vulnerability
- The affected EazyDataFix version
- The Python version and operating system
- Minimal reproduction steps or a proof of concept
- Expected and observed behaviour
- The potential impact
- Relevant logs, traces, or screenshots with secrets and personal data removed
- A suggested mitigation, when known

## Data and Privacy

Security reports must not contain:

- Real credentials, tokens, secrets, or API keys
- Private, confidential, regulated, or personally identifiable datasets
- Unredacted customer or organisational data

Use synthetic or anonymised examples wherever possible. Redact sensitive values
from proof-of-concept code, logs, traces, screenshots, and report artifacts.

## What Happens Next

After a private report is submitted:

- Maintainers review the report privately.
- They may request clarification or additional reproduction details.
- They assess severity, affected versions, and possible mitigations.
- A fix and coordinated disclosure may be prepared when appropriate.
- The reporter may receive acknowledgement or credit unless anonymity is
  requested.

The appropriate response depends on the report and its impact; no fixed response
or resolution time is promised.

## Coordinated Disclosure

Please do not publish vulnerability details until maintainers have had a
reasonable opportunity to investigate and prepare mitigations. Coordinate
disclosure timing through the private vulnerability report.

## Scope

Security reports may include:

- Unsafe handling of files or paths
- Arbitrary code execution
- Dependency-related exposure that directly affects EazyDataFix
- Sensitive data leakage
- Insecure temporary-file or report handling
- Vulnerabilities in public APIs or deterministic data-processing workflows
- Security weaknesses introduced through optional integrations

## Non-Security Reports

Use the repository's existing GitHub Issue Forms for ordinary bugs, feature
requests, documentation issues, and usage questions. Do not include suspected
vulnerability details in a public issue.
