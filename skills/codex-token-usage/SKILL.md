---
name: codex-token-usage
description: Show the user's local Codex prompt token usage and 5-hour and 7-day limit percentages when they ask for a usage report.
---

# Codex token usage

When asked for Codex prompt usage, run `codex_token_usage.py` at the plugin root (two directories above this file) with Python 3. Set `--output` to a temporary path unless the user asks to save the TSV. Use `--sessions 1` for the current session or more when the user asks for history.

Read only local Codex session logs. Do not transmit prompt text or the TSV. Percentage-point changes come from rounded logged values; an ongoing response may lack a completion time. If local execution is unavailable, explain the limitation instead of estimating usage.

Respond in English. Preserve the original prompt text without translating it.
