"""Official exhibition listing adapters. Only dated, physical exhibitions are emitted."""
import re
import time
from datetime import date
from urllib.parse import urljoin, urlparse
from functools import partial
import requests
from bs4 import BeautifulSoup
from normalize import event, MONTHS

URLS = {
    'V&A': 'https://www.vam.ac.uk/whatson',
    'Design Museum': 'https://designmuseum.org/exhibitions',
    'Serpentine': 'https://www.serpentinegalleries.org/whats-on/',
    'Whitechapel Gallery': 'https://www.whitechapelgallery.org/exhibitions/',
    "The Photographers' Gallery": 'https://thephotographersgallery.org.uk/whats-on',
    'Courtauld Gallery': 'https://courtauld.ac.uk/whats-on/',
}
MONTH = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Sept|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
DATE = re.compile(r'(\d{1,2})\s+(' + MONTH + r')(?:\s+(\d{4}))?', re.I)

def dates(text):
    """No invented day/month. Infer omitted start year, including an Oct–Feb run."""
    text = re.sub(r'\s+', ' ', text or '')
    tokens = list(DATE.finditer(text))
    if not tokens or not tokens[-1][3]:
        return None, None
    def value(m, year):
        return date(int(m[3] or year), MONTHS[m[2].lower()], int(m[1]))
    try:
        end = value(tokens[-1], int(tokens[-1][3]))
        if len(tokens) >= 2:
            first = tokens[0]
            start = value(first, end.year)
            if start > end and not first[3]:
                start = value(first, end.year - 1)
            if start > end:
                return None, None
            return start.isoformat(), end.isoformat()
        if re.search(r'until|closes|ends', text, re.I):
            return None, end.isoformat()
    except (ValueError, KeyError):
        pass
    return None, None

def txt(card, selector):
    el = card.select_one(selector)
    return el.get_text(' ', strip=True) if el else ''

def parse(name, html):
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    if name == 'V&A':
        cards = soup.select('a.exhibiton-carousel-card')
    elif name == 'Design Museum':
        cards = soup.select('.page-item')
    elif name == 'Serpentine':
        cards = soup.select('section.teaser')
    elif name == 'Whitechapel Gallery':
        cards = soup.select('.mediaBlock')
    elif name == "The Photographers' Gallery":
        cards = soup.select('article.o-teaser')
    else:
        cards = soup.select('article.o-featured-teaser')
    for card in cards:
        venue, price = name, ''
        if name == 'V&A':
            link = card
            title = txt(card, 'h3')
            raw = txt(card, '[title="Calendar timing"]')
            venue = txt(card, '[title="Venue location"]')
            if venue not in ('Young V&A', 'V&A South Kensington', 'V&A East Museum'):
                continue
            price = txt(card, '[title="Admission fee"]')
        elif name == 'Design Museum':
            link = card.select_one('a[href^="/exhibitions/"]')
            title, raw = txt(card, 'h2'), txt(card, 'time')
            if 'free' in raw.lower():
                price = 'Free'
        elif name == 'Serpentine':
            if not card.select_one('a[href*="type=exhibitions"]'):
                continue
            link = card.select_one('h3 a')
            title, raw = txt(card, 'h3'), txt(card, '.meta')
            venue = txt(card, '.meta__term')
            if venue not in ('Serpentine North Gallery', 'Serpentine South Gallery'):
                continue
            if 'Free' in raw:
                price = 'Free'
        elif name == 'Whitechapel Gallery':
            link = card.select_one('h4.category_name a')
            title, raw = txt(card, 'h4.category_name'), txt(card, 'p')
        elif name == "The Photographers' Gallery":
            if txt(card, '.o-teaser__post-type') not in ('Exhibition', 'Soho Photography Quarter'):
                continue
            link = card.select_one('.o-teaser__title a')
            title, raw = txt(card, '.o-teaser__title'), txt(card, '.o-teaser__date')
        else:
            if 'Exhibition' not in txt(card, '.tag'):
                continue
            link = card.select_one('h2 a')
            title = txt(card, 'h2')
            raw = ' '.join(p.get_text(' ', strip=True) for p in card.select('.o-featured-teaser__content > p:not(.tag)'))
        start, end = dates(raw)
        if not title or link is None or not end:
            continue
        out.append(event('exhibition', title, urljoin(URLS[name], link['href']), name,
                         etype='Exhibition', venue=venue, area='London',
                         start=start, end=end, date_text=raw, price=price))
    return out

def fetch(name):
    url = URLS[name]
    out = []
    for _ in range(5):
        r = requests.get(url, timeout=35)
        r.raise_for_status()
        out.extend(parse(name, r.text))
        next_link = BeautifulSoup(r.text, 'html.parser').select_one('a[rel="next"]') if name == "The Photographers' Gallery" else None
        if not next_link:
            break
        url = urljoin(url, next_link['href'])
        if urlparse(url).netloc != urlparse(URLS[name]).netloc:
            raise RuntimeError('Unexpected pagination host')
        time.sleep(0.3)
    return out

SOURCES = [(name, partial(fetch, name)) for name in URLS]
