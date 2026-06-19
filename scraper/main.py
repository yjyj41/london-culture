#!/usr/bin/env python3
"""
London Culture — aggregator entry point.

Runs every source, merges + de-duplicates, drops anything already finished,
and writes ../docs/events.json for the static site to read.

Each source is isolated: if one fails, the others still produce a file.
"""
import os
import sys
import json
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(__file__))

from sources import (ticketmaster, tate, national_gallery, wigmore,
                     barbican, timeout)

SOURCES = [
    ('Ticketmaster', ticketmaster.fetch),
    ('Tate', tate.fetch),
    ('National Gallery', national_gallery.fetch),
    ('Wigmore Hall', wigmore.fetch),
    ('Barbican', barbican.fetch),
    ('Time Out', timeout.fetch),
]

OUT = os.path.join(os.path.dirname(__file__), '..', 'docs', 'events.json')


def still_relevant(ev, today):
    """Keep events with no end date, or ending today or later."""
    if not ev.get('end'):
        return True
    try:
        return datetime.strptime(ev['end'], '%Y-%m-%d').date() >= today
    except ValueError:
        return True


def main():
    today = date.today()
    all_events = []
    for name, fn in SOURCES:
        try:
            all_events.extend(fn() or [])
        except Exception as e:
            print(f'  [{name}] FAILED: {e}')

    # de-duplicate by id, then by (title, start)
    seen, deduped = set(), []
    for ev in all_events:
        key = ev['id']
        alt = (ev['title'].lower(), ev.get('start'))
        if key in seen or alt in seen:
            continue
        seen.add(key)
        seen.add(alt)
        if still_relevant(ev, today):
            deduped.append(ev)

    # sort: dated events first (ascending), undated last
    deduped.sort(key=lambda e: (e.get('start') is None, e.get('start') or ''))

    payload = {
        'updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
        'count': len(deduped),
        'events': deduped,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f'\n== wrote {len(deduped)} events to {os.path.relpath(OUT)} ==')


if __name__ == '__main__':
    main()
