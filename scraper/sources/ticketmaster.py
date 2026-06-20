"""
Ticketmaster Discovery API.

Used here in a FOCUSED way so it doesn't flood the archive (a broad London
"Music" pull returns ~700 events). We fetch:
  1. ALL London jazz   (classificationName=Jazz)         -> the user's ask
  2. A small sample of upcoming concerts (segmentName=Music, 1 page)

Free key: https://developer.ticketmaster.com/  -> env var TICKETMASTER_API_KEY
Free tier: 5000 calls/day, 5 req/sec.
"""
import os
import time
import requests
from normalize import event

API = 'https://app.ticketmaster.com/discovery/v2/events.json'

# (label, extra query params, max pages to pull)
QUERIES = [
    ('Jazz',     {'classificationName': 'Jazz'}, 3),   # all jazz in London
    ('Concerts', {'segmentName': 'Music'},       1),   # small concert sample
]


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
    for label, extra, max_pages in QUERIES:
        page = 0
        while page < max_pages:
            params = {
                'apikey': key,
                'city': 'London',
                'countryCode': 'GB',
                'sort': 'date,asc',
                'size': 100,
                'page': page,
                'startDateTime': time.strftime('%Y-%m-%dT00:00:00Z'),
                **extra,
            }
            try:
                r = requests.get(API, params=params, timeout=30)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f'  [ticketmaster] {label} page {page} error: {e}')
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
                sdate = (ev.get('dates') or {}).get('start', {})
                start = sdate.get('localDate')
                ltime = (sdate.get('localTime') or '')[:5]  # "19:30"
                etype = genre if genre and genre != 'Undefined' else label
                out.append(event(
                    category='music',
                    title=ev.get('name', ''),
                    url=ev.get('url', ''),
                    source='Ticketmaster',
                    etype=etype,
                    venue=venue,
                    area=area,
                    start=start,
                    end=start,
                    time=ltime,
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
