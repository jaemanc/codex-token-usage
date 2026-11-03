---
name: codex-token-usage
description: Show the user's local Codex prompt token usage and 5-hour and 7-day limit percentages when they ask for a usage report.
---

# Codex token usage

When the user asks for their Codex prompt usage, run `codex_token_usage.py` next to this file with Python 3. Set `--output` to a temporary path unless the user asks to save the TSV. Use `--sessions 1` for the current session or more when the user asks for history.

Read only local Codex session logs. Do not transmit prompt text or the TSV. Report that percentage-point changes come from rounded logged values and that an ongoing response may lack a completion time. If the script is unavailable, explain where to install it rather than estimating usage.
