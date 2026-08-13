# Security policy

## Supported versions

Security fixes are applied to the latest version on the default branch.

## Reporting a vulnerability

Do not open a public issue for an undisclosed vulnerability. Use the repository host's private security-advisory feature and include:

- the affected file and version or commit;
- reproduction steps and realistic impact;
- any suggested mitigation;
- whether the issue is already public.

Maintainers should acknowledge a complete report within seven days. No response-time or bounty guarantee is made.

## Scope

The skill contains instructions and local validation utilities. It does not require secrets, telemetry, network services, or runtime dependencies. Benchmarking invokes the user's installed Codex CLI and inherits that tool's authentication and sandbox controls.
