"""Public venue/producer listings; bounded pagination and explicit performance spans."""
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from functools import partial
import requests
from bs4 import BeautifulSoup
from normalize import event, MONTHS
from curation import classify, matches, PREFERENCES

URLS = {'Vortex': 'https://www.vortexjazz.co.uk/event/',
        "Ronnie Scott's": 'https://www.ronniescotts.co.uk/find-a-show',
        'EartH': 'https://earthackney.co.uk/events/',
        'Serious': 'https://serious.org.uk/whats-on/upcoming-events'}
LONDON_VENUES = {'Jazz Cafe', 'EartH (Theatre)', 'Cadogan Hall', 'LONDON Stone Nest', 'KOKO', 'Barbican',
                 'Royal Albert Hall', 'Royal Festival Hall', 'Union Chapel', 'Kings Place'}
NOT_MUSIC = re.compile(r'\b(comedy|comedian|podcast|workshop|book launch|book club|panel|talks?|screening|film screening|downstream irl|fundraiser)\b', re.I)
MUSIC = re.compile(r'\b(jazz|music|musician|singer|band|guitarist|pianist|album|saxophonist|composer|folk|concert|live set|quartet|trio|vocalist)\b', re.I)

def text(card, selector):
    node = card.select_one(selector)
    return node.get_text(' ', strip=True) if node else ''

def clock(raw):
    # Vortex prints 7.45 - 10.30PM. Infer the shared suffix only for unambiguous same-half-day spans.
    m = re.search(r'(\d{1,2})(?:[.:](\d{2}))?\s*(AM|PM)?\s*[-–]\s*(\d{1,2})(?:[.:](\d{2}))?\s*(AM|PM)', raw, re.I)
    if not m:
        return ''
    h, minute = int(m[1]), int(m[2] or 0)
    suffix = m[3] or (m[6] if h <= int(m[4]) and h != 12 else None)
    if not suffix or not 1 <= h <= 12 or minute > 59:
        return ''
    return f"{h % 12 + (12 if suffix.upper() == 'PM' else 0):02d}:{minute:02d}"

def ronnie_dates(raw):
    # Preserve advertised date spans; never turn recurring Wednesdays into daily gigs.
    raw = re.sub(r'(?<=\d)(?=[A-Za-z])|(?<=[A-Za-z])(?=\d)', ' ', raw)
    short = re.search(r'(\d{1,2})\s*[-–]\s*(?:[A-Za-z]{3}\s+)?\d{1,2}\s+([A-Za-z]+)', raw)
    if short and short[2].lower() in MONTHS:
        raw = raw[:short.start()] + short[1] + ' ' + short[2] + raw[short.end(1):]
    tokens = re.findall(r'(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?', raw)
    tokens = [t for t in tokens if t[1].lower() in MONTHS]
    if not tokens or not tokens[-1][2]:
        return None, None
    year = int(tokens[-1][2])
    def dt(t, y): return datetime(int(t[2] or y), MONTHS[t[1].lower()], int(t[0])).date()
    try:
        end = dt(tokens[-1], year); start = dt(tokens[0], year)
        if start > end and not tokens[0][2]: start = dt(tokens[0], year-1)
        return start.isoformat(), end.isoformat()
    except ValueError:
        return None, None

def parse(name, html):
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    if name == 'Vortex':
        for card in soup.select('article.type-tribe_events'):
            heading = card.find_previous('h2', class_='event_list_date')
            link = card.select_one('a.post_title')
            if not heading or not link: continue
            title = link.get_text(' ', strip=True)
            if NOT_MUSIC.search(title + ' ' + text(card, '.event_tags')): continue
            dt = datetime.strptime(heading.get_text(' ', strip=True), '%a %d %B %Y').date().isoformat()
            raw_time = text(card, '.event_time')
            ev = event('music', title, link['href'], name, etype='Jazz', venue='Vortex', area='London',
                       start=dt, end=dt, time=clock(raw_time), price=text(card,'.event_price'))
            if not ev['time']: ev['subtitle'] = raw_time
            ev['jazz_venue_listing'] = True
            out.append(ev)
    elif name == "Ronnie Scott's":
        for card in soup.select('.listing'):
            link = card.select_one('a[href*="/find-a-show/"]')
            title = text(card, '.listing__title')
            direct = card.find_all('div', recursive=False)
            raw = next((d.get_text(' ', strip=True) for d in direct if re.search(r'\d{4}', d.get_text()) and not d.select_one('button')), '')
            start, end = ronnie_dates(raw)
            if not link or not title or not end or NOT_MUSIC.search(title): continue
            ev = event('music', title, link['href'], name, etype='Jazz', venue="Ronnie Scott's",
                       area='London', start=start, end=end, date_text=raw,
                       subtitle=text(card, '.listing__show-type'))
            ev.update(jazz_venue_listing=True, schedule_note='공연 기간 · 개별 날짜와 회차는 원본에서 확인' if start != end else '회차와 시작 시간은 원본에서 확인')
            out.append(ev)
    elif name == 'EartH':
        for card in soup.select('li.list--events__item'):
            title = text(card, 'h3')
            description = text(card, '.list--events__item__description')
            if NOT_MUSIC.search(title): continue
            if not MUSIC.search(description + ' ' + title) and not re.search(r'k-?pop|k-music', title, re.I) and not matches(title, PREFERENCES['korean_artists'] + PREFERENCES['headline_artists']): continue
            link = card.select_one('a[href*="/events/"]')
            stamp = card.select_one('time[datetime]')
            venue_link = card.select_one('a[href*="/venue/"]')
            if not link or not stamp: continue
            dt = datetime.fromisoformat(stamp['datetime']).date().isoformat()
            tm = re.search(r'\d{1,2}:\d{2}', text(card,'time.time'))
            venue = 'EartH Theatre' if venue_link and 'earth-theatre' in venue_link['href'] else 'EartH Hall' if venue_link and 'earth-hall' in venue_link['href'] else 'EartH'
            genre = 'Jazz' if re.search(r'\bjazz\b', title+' '+description, re.I) else 'Other'
            ev = event('music', title, link['href'], name, etype=genre, venue=venue, area='London',
                       start=dt, end=dt, time=tm[0] if tm else '')
            ev.update(discovery=True, schedule_note='공연장 공지 시간 · 입장과 공연 시작 시간은 원본 확인')
            out.append(ev)
    else:
        for card in soup.select('a.listing-event'):
            venue = text(card, 'span.min-width-pill')
            if venue not in LONDON_VENUES: continue
            times = card.select('time[datetime]')
            title = text(card,'h2')
            if not times or NOT_MUSIC.search(title): continue
            dates = [t['datetime'][:10] for t in times]
            ev = event('music', title, card['href'], name, etype='Other',
                       venue=venue.replace('LONDON ', '').replace('EartH (Theatre)', 'EartH Theatre'),
                       area='London', start=min(dates), end=max(dates))
            ev['discovery'] = True
            out.append(ev)
    for row in out: row['url'] = urljoin(URLS[name], row['url'])
    return out

def fetch(name):
    url = URLS[name]
    out, visited = [], set()
    for _ in range(30):
        if url in visited: raise RuntimeError('Repeated listing page')
        visited.add(url)
        r = requests.get(url, timeout=35)
        r.raise_for_status()
        rows = parse(name, r.text)
        if not rows and not out: raise RuntimeError('No dated event cards returned')
        out.extend(rows)
        soup = BeautifulSoup(r.text, 'html.parser')
        next_link = next((a for a in soup.select('a[href]') if a.get_text(' ',strip=True) in ('Next Page','Next')), None) if name in ('Vortex',"Ronnie Scott's") else None
        if not next_link: break
        url = urljoin(url,next_link['href'])
        if urlparse(url).netloc != urlparse(URLS[name]).netloc: raise RuntimeError('Unexpected pagination host')
        time.sleep(.3)
    else: raise RuntimeError('Pagination exceeded 30 pages')
    for row in out: row['url'] = urljoin(URLS[name], row['url'])
    return out

SOURCES = [(name, partial(fetch,name)) for name in URLS]


