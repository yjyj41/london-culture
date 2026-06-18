"""
National Gallery exhibitions.
Listing page is server-rendered. Each exhibition is an <a> whose text reads
roughly:  "<£|Free> Exhibition <Title> <DateRange|Until ...> <Description>".
We split that with a date regex.
"""
import re
import requests
from bs4 import BeautifulSoup
from normalize import event

LISTING = 'https://www.nationalgallery.org.uk/exhibitions'
BASE = 'https://www.nationalgallery.org.uk'
HEADERS = {'User-Agent': 'london-culture-bot/1.0 (personal archive)'}

DASH = r'[–—‒‑‐−-]'
DATE_RE = re.compile(
    r'(Until\s+\d{1,2}\s+[A-Z][a-z]+\s+\d{4}'
    r'|\d{1,2}\s+[A-Z][a-z]+(?:\s+\d{4})?\s*' + DASH +
    r'\s*\d{1,2}\s+[A-Z][a-z]+\s+\d{4})')
PREFIX_RE = re.compile(r'^\s*(£|Free)\s*Exhibition', re.I)

SKIP = {'/exhibitions', '/exhibitions/past', '/exhibitions/across-the-uk'}


def fetch():
    try:
        r = requests.get(LISTING, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f'  [national-gallery] listing error: {e}')
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    out, seen = [], set()

    for a in soup.find_all('a', href=True):
        path = a['href'].split('?')[0].rstrip('/')
        if '/exhibitions/' not in path or path in SKIP:
            continue
        text = a.get_text(' ', strip=True)
        if 'Exhibition' not in text:
            continue

        url = path if path.startswith('http') else BASE + path
        if url in seen:
            continue

        pm = PREFIX_RE.match(text)
        price = '' if not pm else ('Free' if pm.group(1).lower() == 'free' else '£')
        body = PREFIX_RE.sub('', text).strip()

        dm = DATE_RE.search(body)
        if not dm:
            continue  # need a date to be a real listing
        title = body[:dm.start()].strip()
        date_text = dm.group(0)
        if not title:
            continue

        seen.add(url)
        out.append(event('exhibition', title, url, 'National Gallery',
                         etype='Exhibition', venue='National Gallery',
                         area='London', date_text=date_text, price=price))

    print(f'  [national-gallery] {len(out)} events')
    return out
