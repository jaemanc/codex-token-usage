#!/usr/bin/env python3
"""Show Codex prompts and measured token deltas; export one TSV row per prompt."""
import argparse
import csv
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens')

def local_time(value):
    if not value:
        return '진행 중'
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone().strftime('%m-%d %H:%M:%S')

def prompt_lines(text, width, limit):
    text = text[:limit].rstrip() + ('…' if len(text) > limit else '')
    lines, line, used = [], '', 0
    for char in text:
        size = 2 if unicodedata.east_asian_width(char) in ('F', 'W') else 1
        if used + size > width:
            lines.append(line)
            line, used = '', 0
        line += char
        used += size
    return lines + [line] if line else lines

def as_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '\n'.join(filter(None, map(as_text, value)))
    if isinstance(value, dict):
        if value.get('type') in ('input_text', 'text', 'output_text'):
            return str(value.get('text') or '')
        return as_text(value.get('content'))
    return ''

def read_session(path):
    records = []
    active = None
    last_counters = None
    last_limits = {}
    seen_item_ids = set()
    for line in path.open(encoding='utf-8', errors='replace'):
        try:
            obj = json.loads(line)
        except (ValueError, TypeError):
            continue
        kind, payload = obj.get('type'), obj.get('payload')
        if not isinstance(payload, dict):
            continue

        # Codex's actual session event: response_item/message role=user.
        # item_completed is not treated as user prompt to avoid duplicate records.
        if kind == 'response_item' and payload.get('type') == 'message' and payload.get('role') == 'user':
            prompt = as_text(payload.get('content')).strip()
            if not prompt:
                continue
            item_id = payload.get('id')
            if item_id and item_id in seen_item_ids:
                continue
            if item_id:
                seen_item_ids.add(item_id)
            active = dict(prompt_time=obj.get('timestamp') or '', response_time='', prompt=prompt,
                          input=0, cached=0, output=0, events=0,
                          limit_start=last_limits.copy(), limit_end=last_limits.copy())
            records.append(active)
            continue

        if kind == 'event_msg' and payload.get('type') == 'task_complete' and active is not None:
            active['response_time'] = obj.get('timestamp') or ''
            active = None
            continue

        if kind == 'event_msg' and payload.get('type') == 'token_count':
            limits = payload.get('rate_limits') or {}
            for key in ('primary', 'secondary'):
                value = (limits.get(key) or {}).get('used_percent')
                if isinstance(value, (int, float)):
                    if active is not None and key not in active['limit_start']:
                        active['limit_start'][key] = value
                    last_limits[key] = value
                    if active is not None:
                        active['limit_end'][key] = value
            info = payload.get('info') or {}
            usage = info.get('total_token_usage') if isinstance(info, dict) else None
            if not isinstance(usage, dict):
                continue
            try:
                counters = tuple(int(usage.get(k) or 0) for k in KEYS)
            except (TypeError, ValueError):
                continue
            # First reading can be a snapshot from work preceding the first logged prompt.
            # Treat it as a baseline, not as this prompt's usage.
            if last_counters is None:
                last_counters = counters
                continue
            if any(n < p for n, p in zip(counters, last_counters)):
                last_counters = counters
                continue  # reset; do not attribute the whole counter to one prompt
            delta = [n-p for n,p in zip(counters, last_counters)]
            last_counters = counters
            if active is not None and any(delta):
                active['input'] += delta[0]
                active['cached'] += delta[1]
                active['output'] += delta[2]
                active['events'] += 1

    for r in records:
        r['total'] = r['input'] + r['output']
        r['new_input'] = r['input'] - r['cached']
        for key, name, cumulative in (('primary', 'five_hour_percent', 'five_hour_used_percent'),
                                      ('secondary', 'seven_day_percent', 'seven_day_used_percent')):
            start, end = r['limit_start'].get(key), r['limit_end'].get(key)
            r[name] = round(end - start, 1) if start is not None and end is not None and end >= start else ''
            r[cumulative] = end if end is not None else ''
    return records

def main():
    ap = argparse.ArgumentParser(description='Codex user prompts + measured tokens (one row each)')
    ap.add_argument('--sessions', type=int, default=5)
    ap.add_argument('--chars', type=int, default=240)
    ap.add_argument('--output', default='codex_prompt_tokens.tsv')
    ap.add_argument('--root', type=Path, default=Path.home()/'.codex'/'sessions')
    args = ap.parse_args()
    paths = sorted(args.root.rglob('*.jsonl'), key=lambda p:p.stat().st_mtime, reverse=True)[:args.sessions]
    records = [r for p in paths for r in read_session(p)]
    valid = [r for r in records if r['events'] > 0]
    cols = ('prompt_time','response_time','prompt','input','cached','new_input','output','total','events',
            'five_hour_percent','five_hour_used_percent','seven_day_percent','seven_day_used_percent')
    with Path(args.output).expanduser().open('w', encoding='utf-8-sig', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=cols, delimiter='\t', extrasaction='ignore')
        wr.writeheader()
        wr.writerows(valid)
    width = max(30, shutil.get_terminal_size(fallback=(100, 24)).columns - 5)
    for i, r in enumerate(valid, 1):
        prompt = re.sub(r'\s+', ' ', re.sub(r'</?image\b[^>]*>', lambda m: '' if m.group().startswith('</') else '[이미지]', r['prompt'])).strip()
        print(f"{i:>3}. 작성 {local_time(r['prompt_time'])} → 응답 {local_time(r['response_time'])}")
        for line in prompt_lines(prompt, width, args.chars):
            print(f"     {line}")
        print(f"     입력 {r['input']:,} (캐시 {r['cached']:,}, 신규 {r['new_input']:,})  출력 {r['output']:,}  합계 {r['total']:,}  이벤트 {r['events']}")
        for label, delta_key, used_key in (('5시간', 'five_hour_percent', 'five_hour_used_percent'),
                                           ('7일', 'seven_day_percent', 'seven_day_used_percent')):
            delta = f"+{r[delta_key]:.1f}%p" if r[delta_key] != '' else '기록 없음'
            used = f"{r[used_key]:.1f}%" if r[used_key] != '' else '기록 없음'
            print(f"     {label} 한도: 이번 요청 {delta} · 누적 {used}")
    print(f'\n{len(valid)} matched prompts; {len(records)-len(valid)} prompts without measurable token deltas omitted; TSV: {args.output}', file=sys.stderr)
    if not valid:
        print('No matched records: actual JSONL may use a different token or prompt schema.', file=sys.stderr)

if __name__ == '__main__':
    main()

