# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability, please do **not** open a public GitHub issue.

Instead, report it privately:

1. Go to the [Security tab](https://github.com/rmolines/claude-kickstart/security/advisories/new) of this repository
2. Click "Report a vulnerability"
3. Describe the issue with as much detail as possible

You will receive a response within 72 hours. If confirmed, a patch will be released as quickly as possible.

## Scope

This is a GitHub Template Repository — it contains no runtime code or live infrastructure.

Relevant security concerns:

- **Shell hook injection**: hooks in `.claude/settings.json` execute shell commands. See [CVE-2025-59536](https://github.com/advisories) for context.
- **GitHub Actions supply chain**: actions are pinned to full commit SHAs to prevent tag hijacking.
- **Template sync**: the `template-sync.yml` workflow pulls files from upstream. Review all PRs it creates before merging.

## Supported versions

This template is a living document. Always use the latest version from `main`.
