#!/usr/bin/env python3
"""Daily aggregation with source-level freshness and bounded last-good retention."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
from sources import ticketmaster, tate, national_gallery, wigmore, barbican, bachtrack
from curation import classify, folded

SOURCES = [('Bachtrack', bachtrack.fetch), ('Wigmore Hall', wigmore.fetch),
           ('Barbican', barbican.fetch), ('Tate', tate.fetch),
           ('National Gallery', national_gallery.fetch), ('Ticketmaster', ticketmaster.fetch)]
OUT = Path(__file__).resolve().parent.parent / 'docs' / 'events.json'
RETENTION_DAYS = 7

def still_relevant(ev, today):
    value = ev.get('end') or ev.get('start')
    try:
        return bool(value) and date.fromisoformat(value) >= today
    except (ValueError, TypeError):
        return False

def collect(previous, sources=SOURCES, now=None):
    now = now or datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo('Europe/London')).date()
    stamp = now.isoformat(timespec='seconds')
    events, statuses = [], []
    old_status = {s['name']: s for s in previous.get('sources', [])}
    for name, fn in sources:
        old = [e for e in previous.get('events', []) if e.get('source') == name]
        last_success = old_status.get(name, {}).get('last_success')
        if not last_success and old:
            # Migrate the original payload's timestamp without making it appear newly fetched.
            try:
                last_success = datetime.strptime(previous['updated'], '%Y-%m-%d %H:%M UTC').replace(tzinfo=timezone.utc).isoformat()
            except (KeyError, ValueError):
                pass
        error = None
        try:
            raw = fn()
            if not raw and name != 'Ticketmaster':
                raise RuntimeError('No cards returned; source may be unavailable or changed')
            fresh = [dict(e, last_seen=stamp, stale=False) for e in raw]
            last_success = stamp
        except Exception as exc:
            error = str(exc)
            fresh = []
            for ev in old:
                seen = ev.get('last_seen') or last_success
                try:
                    recent = 0 <= (now - datetime.fromisoformat(seen)).total_seconds() <= RETENTION_DAYS * 86400
                except (TypeError, ValueError):
                    recent = False
                if recent:
                    fresh.append(dict(ev, last_seen=seen, stale=True))
        selected = []
        for ev in fresh:
            ev = classify(ev)
            if ev and still_relevant(ev, today):
                selected.append(ev)
        events.extend(selected)
        statuses.append(dict(name=name, status='unavailable' if error else 'ok',
                             count=len(selected), last_success=last_success, checked_at=stamp,
                             message=error or ''))
        print(f"[{name}] {len(selected)} selected; {'unavailable' if error else 'ok'}")
    # Keep separate venues and matinee/evening performances. Prefer freshly checked rows.
    unique = {}
    for ev in sorted(events, key=lambda e: bool(e.get('stale'))):
        key = (folded(ev['title']), folded(ev['venue']), ev.get('start'), ev.get('time'))
        if key not in unique:
            unique[key] = ev
    events = sorted(unique.values(), key=lambda e: (e.get('start') or e.get('end'), e.get('time') or ''))
    return dict(updated=stamp, count=len(events), sources=statuses, events=events)

def main():
    try:
        previous = json.loads(OUT.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        previous = {}
    payload = collect(previous)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(OUT)
    print(f"Wrote {payload['count']} events")

if __name__ == '__main__':
    main()
