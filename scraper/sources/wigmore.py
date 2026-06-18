"""
Wigmore Hall — classical concerts / recitals (London).

Replaces Bachtrack (which has no API and a JavaScript-only search form that
resists scraping). Wigmore Hall's /whats-on page is server-rendered and, even
better, every event link encodes its date+time in the URL, e.g.
    /whats-on/202606181930   ->  2026-06-18 19:30
so dates are 100% reliable and we never have to parse fuzzy text.
"""
import re
import requests
from bs4 import BeautifulSoup
from normalize import event

LISTING = 'https://www.wigmore-hall.org.uk/whats-on'
BASE = 'https://www.wigmore-hall.org.uk'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/124.0 Safari/537.36',
    'Accept-Language': 'en-GB,en;q=0.9',
}

# event links look like /whats-on/202606181930  (YYYYMMDDHHMM)
HREF_RE = re.compile(r'^/whats-on/(\d{8})(\d{4})$')


def _date_from_href(href):
    m = HREF_RE.match(href)
    if not m:
        return None, None
    d, t = m.group(1), m.group(2)
    iso = f'{d[0:4]}-{d[4:6]}-{d[6:8]}'
    pretty = f'{d[6:8]}.{d[4:6]}.{d[0:4]} {t[0:2]}:{t[2:4]}'
    return iso, pretty


def fetch():
    try:
        r = requests.get(LISTING, headers=HEADERS, timeout=40)
        r.raise_for_status()
    except Exception as e:
        print(f'  [wigmore] listing error: {e}')
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    out, seen = [], set()

    for a in soup.find_all('a', href=True):
        href = a['href'].split('?')[0]
        iso, pretty = _date_from_href(href)
        if not iso or href in seen:
            continue

        # Title = first non-empty line of the link text. The link also holds
        # performer/instrument lines; we keep the headline only.
        lines = [ln.strip() for ln in a.get_text('\n', strip=True).split('\n')
                 if ln.strip()]
        if not lines:
            continue
        title = lines[0]
        # the remaining lines (performers / instruments) make a useful subtitle
        subtitle = ', '.join(lines[1:4]) if len(lines) > 1 else ''
        if title.lower().startswith('cancelled'):
            continue

        seen.add(href)
        out.append(event('music', title, BASE + href, 'Wigmore Hall',
                         subtitle=subtitle, etype='Classical',
                         venue='Wigmore Hall', area='London',
                         start=iso, end=iso, date_text=pretty))

    print(f'  [wigmore] {len(out)} events')
    return out
