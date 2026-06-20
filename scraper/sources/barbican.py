"""
Barbican Centre — multi-arts (classical & contemporary music, cinema,
theatre & dance, art & design, talks, immersive).

The /whats-on page is server-rendered. Each card is
    <div class="search-listing search-listing--event panel">
with:
    category  -> span.tag__plain          ("Classical music", "Cinema", ...)
    title     -> h2.listing-title
    date      -> <time datetime="2026-06-19T08:30:00Z">  (clean ISO)
    link      -> a href="/whats-on/2026/event/<slug>"
Events repeating on several days appear once per day, so we de-duplicate by
slug and keep the earliest/latest dates as the run's start/end.
"""
import re
import requests
from bs4 import BeautifulSoup
from normalize import event

# parse a human time like "9.30am" / "7.30pm" into 24h "09:30" / "19:30"
TIME_RE = re.compile(r'(\d{1,2})[.:](\d{2})\s*(am|pm)', re.I)


def _time24(text):
    m = TIME_RE.search(text or '')
    if not m:
        return ''
    h, mn, ap = int(m.group(1)), m.group(2), m.group(3).lower()
    if ap == 'pm' and h != 12:
        h += 12
    if ap == 'am' and h == 12:
        h = 0
    return f'{h:02d}:{mn}'

LISTING = 'https://www.barbican.org.uk/whats-on'
BASE = 'https://www.barbican.org.uk'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/124.0 Safari/537.36',
    'Accept-Language': 'en-GB,en;q=0.9',
}


def _category(text):
    c = (text or '').lower()
    if 'music' in c:
        return 'music'
    if 'art' in c or 'design' in c:
        return 'exhibition'
    if 'theatre' in c or 'dance' in c:
        return 'theatre'
    return 'event'


def fetch():
    try:
        r = requests.get(LISTING, headers=HEADERS, timeout=40)
        r.raise_for_status()
    except Exception as e:
        print(f'  [barbican] listing error: {e}')
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    by_slug = {}

    for card in soup.select('.search-listing--event'):
        a = card.find('a', href=True)
        title_el = card.select_one('.listing-title')
        if not a or not title_el:
            continue
        href = a['href'].split('?')[0]
        if '/event/' not in href:
            continue
        slug = href.rstrip('/').split('/')[-1]
        title = title_el.get_text(' ', strip=True)
        if not title:
            continue

        cat_el = card.select_one('.tag__plain')
        cat_text = cat_el.get_text(' ', strip=True) if cat_el else ''

        # collect ISO dates from <time datetime="...">
        time_tags = card.find_all('time')
        dates = sorted(
            t['datetime'][:10] for t in time_tags
            if t.get('datetime') and len(t['datetime']) >= 10
        )
        start = dates[0] if dates else None
        end = dates[-1] if dates else None
        # time = human text on the card ("9.30am"), already local London time
        clock = _time24(time_tags[0].get_text(' ', strip=True)) if time_tags else ''

        rec = by_slug.get(slug)
        if rec:
            # merge date span across repeated cards
            if start and (not rec['start'] or start < rec['start']):
                rec['start'] = start
            if end and (not rec['end'] or end > rec['end']):
                rec['end'] = end
            continue
        by_slug[slug] = {
            'title': title,
            'url': BASE + href if href.startswith('/') else href,
            'cat': _category(cat_text),
            'type': cat_text or 'Event',
            'start': start,
            'end': end,
            'time': clock,
        }

    out = []
    for rec in by_slug.values():
        dt = ''
        if rec['start']:
            dt = rec['start'] if rec['start'] == rec['end'] else f"{rec['start']} - {rec['end']}"
        out.append(event(rec['cat'], rec['title'], rec['url'], 'Barbican',
                         etype=rec['type'], venue='Barbican Centre', area='London',
                         start=rec['start'], end=rec['end'],
                         time=rec.get('time', ''), date_text=dt))

    print(f'  [barbican] {len(out)} events')
    return out
