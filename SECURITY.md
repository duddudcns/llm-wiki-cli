# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities privately, not as a public GitHub
issue: use this repository's [private vulnerability
reporting](https://github.com/duddudcns/llm-wiki-cli/security/advisories/new)
(GitHub → Security tab → "Report a vulnerability"). This opens a draft
security advisory visible only to the maintainer until a fix ships.

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce it
- The affected version(s)

## Scope

`llmw` is a local CLI that reads and writes Markdown files under a
project's `raw/`/`wiki/`/`.llmw/` directories, and can run as a Claude
Code or Codex plugin with hooks and an MCP server. Reports of particular
interest:

- Path traversal outside the project root
- Arbitrary code execution via crafted wiki content, frontmatter, or CLI
  arguments
- Denial of service via malicious wiki content (e.g. input that triggers
  pathological regex backtracking)
- Anything that lets a malicious wiki page, or a malicious MCP client,
  perform file operations the agent/user didn't intend

## Response

This is a small, community-maintained project without a dedicated
security team or a fixed SLA — but vulnerability reports are treated as
a priority and we'll do our best to acknowledge and address them
promptly.
