"""
Tate (Modern + Britain) exhibitions.
The listing page is server-rendered, and each detail page exposes clean
metadata (og:title, a visible date range, and a price), so we read those.
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from normalize import event

LISTING = ('https://www.tate.org.uk/whats-on'
           '?date_range=from_now&event_type=exhibition')
BASE = 'https://www.tate.org.uk'
HEADERS = {'User-Agent': 'london-culture-bot/1.0 (personal archive)'}

# London galleries only
DETAIL_RE = re.compile(r'/whats-on/(tate-modern|tate-britain)/[a-z0-9-]+$')
DATE_RE = re.compile(
    r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4}\s*[–-]\s*\d{1,2}\s+[A-Z][a-z]+\s+\d{4}'
    r'|Until\s+\d{1,2}\s+[A-Z][a-z]+\s+\d{4})')
PRICE_RE = re.compile(r'£\s?\d+')
GALLERY = {'tate-modern': 'Tate Modern', 'tate-britain': 'Tate Britain'}


def _detail(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f'  [tate] detail error {url}: {e}')
        return None
    soup = BeautifulSoup(r.text, 'html.parser')

    og = soup.find('meta', attrs={'property': 'og:title'})
    title = (og.get('content') if og else '') or ''
    title = title.split('|')[0].strip()
    if not title:
        return None

    text = soup.get_text(' ', strip=True)
    dm = DATE_RE.search(text)
    date_text = dm.group(0) if dm else ''
    pm = PRICE_RE.search(text)
    price = pm.group(0).replace(' ', '') if pm else 'Free'

    slug = url.rstrip('/').split('/')[-2]  # gallery slug
    venue = GALLERY.get(slug, 'Tate')
    return event('exhibition', title, url, 'Tate',
                 etype='Exhibition', venue=venue, area='London',
                 date_text=date_text, price=price)


def fetch():
    try:
        r = requests.get(LISTING, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f'  [tate] listing error: {e}')
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    urls = []
    for a in soup.find_all('a', href=True):
        href = a['href'].split('?')[0]
        if href.startswith('/'):
            href = BASE + href
        if DETAIL_RE.search(href) and href not in urls:
            urls.append(href)

    out = []
    for u in urls:
        ev = _detail(u)
        if ev:
            out.append(ev)
        time.sleep(0.3)
    print(f'  [tate] {len(out)} events')
    return out
