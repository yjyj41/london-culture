"""
Ticketmaster Discovery API  (concerts / theatre).
Most reliable source: official, free API. Get a key at
https://developer.ticketmaster.com/  and set env var TICKETMASTER_API_KEY.

Docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
Free tier: 5000 calls/day, 5 req/sec.
"""
import os
import time
import requests
from normalize import event

API = 'https://app.ticketmaster.com/discovery/v2/events.json'

# Ticketmaster "segment" -> our category
SEGMENT_MAP = {
    'Music': 'music',
    'Arts & Theatre': 'theatre',
}

# Which segments to pull
SEGMENTS = ['Music', 'Arts & Theatre']


def _price(ev):
    pr = ev.get('priceRanges') or []
    if not pr:
        return ''
    mn = pr[0].get('min')
    cur = pr[0].get('currency', 'GBP')
    sym = '£' if cur == 'GBP' else ''
    return f'{sym}{int(mn)}~' if mn else ''


def fetch():
    key = os.environ.get('TICKETMASTER_API_KEY')
    if not key:
        print('  [ticketmaster] TICKETMASTER_API_KEY not set - skipping')
        return []

    out, seen = [], set()
    for seg in SEGMENTS:
        page = 0
        while page < 4:  # cap pages to stay polite
            params = {
                'apikey': key,
                'city': 'London',
                'countryCode': 'GB',
                'segmentName': seg,
                'sort': 'date,asc',
                'size': 100,
                'page': page,
                'startDateTime': time.strftime('%Y-%m-%dT00:00:00Z'),
            }
            try:
                r = requests.get(API, params=params, timeout=30)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f'  [ticketmaster] {seg} page {page} error: {e}')
                break

            events = (data.get('_embedded') or {}).get('events') or []
            for ev in events:
                eid = ev.get('id')
                if eid in seen:
                    continue
                seen.add(eid)
                cls = (ev.get('classifications') or [{}])[0]
                genre = (cls.get('genre') or {}).get('name', '')
                venues = (ev.get('_embedded') or {}).get('venues') or [{}]
                venue = venues[0].get('name', '')
                area = (venues[0].get('city') or {}).get('name', '')
                start = (ev.get('dates') or {}).get('start', {}).get('localDate')
                out.append(event(
                    category=SEGMENT_MAP.get(seg, 'event'),
                    title=ev.get('name', ''),
                    url=ev.get('url', ''),
                    source='Ticketmaster',
                    etype=genre if genre and genre != 'Undefined' else seg,
                    venue=venue,
                    area=area,
                    start=start,
                    end=start,
                    date_text=start or '',
                    price=_price(ev),
                ))

            total = (data.get('page') or {}).get('totalPages', 1)
            page += 1
            if page >= total:
                break
            time.sleep(0.3)

    print(f'  [ticketmaster] {len(out)} events')
    return out
