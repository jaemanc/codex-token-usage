# Codex Token Usage

A local, standard-library Python report for Codex prompts, token usage, and recorded 5-hour / 7-day usage limits.

## Run

Requires Python 3.9+ and local Codex session logs in `~/.codex/sessions`.

```bash
python3 codex_token_usage.py --sessions 5
```

The terminal shows each prompt's creation and response times, a shortened prompt, token counts, and the change in each usage-limit percentage. The complete prompt and numbers are saved to `codex_prompt_tokens.tsv` in the current directory. Keep that TSV private: it contains your prompt text.

Options:

```bash
python3 codex_token_usage.py --sessions 20 --chars 500 --output /tmp/codex-usage.tsv
python3 codex_token_usage.py --root /path/to/codex/sessions
```

No network requests or third-party Python packages are used. The script only reads local JSONL session files and writes the requested TSV.

`+1.0%p` means the recorded limit use rose by one percentage point during that prompt. `0.0%p` can mean the log's rounded percentage did not change. The cumulative percentage is the latest value recorded for that prompt, not an absolute token quota. A response still in progress has no completion time yet. Codex log formats can change, so missing fields are shown as unavailable.

## Codex skill

### Public Plugin Directory submission

This package is a Desktop only, skills-only plugin because it reads local Codex logs through Python. Its listing metadata, icon, [privacy policy](PRIVACY.md), [support page](SUPPORT.md), and [terms](TERMS.md) are included in the repository. The submission ZIP is built from the plugin root and uploaded as **Skills only** in the [OpenAI plugin submission portal](https://platform.openai.com/plugins). Developer identity verification, portal checks, review, and publication are separate steps.

After publication, users can install it from the ChatGPT desktop Plugin Directory. It runs on demand in a local thread; it does not add a footer to every response.


### Plugin installation (recommended)

```bash
codex plugin marketplace add jaemanc/codex-token-usage
codex plugin add codex-token-usage@codex-token-usage
```

Start a new Codex conversation, then ask for your Codex token usage or invoke `$codex-token-usage`. The plugin runs the local script on demand. You can also open Codex's plugin browser after adding the marketplace and install it there.

### Standalone skill

Clone the repository directly into `~/.codex/skills/codex-token-usage` if you prefer a plain skill without the plugin marketplace.

Neither installation method automatically appends a footer to every Codex response; that requires a separate client or hook integration.
