"""Parse public Bachtrack concert listings and their visible More results endpoint."""
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from normalize import event

URL = 'https://bachtrack.com/search-concerts/city=london'
LONDON = ZoneInfo('Europe/London')
MAX_PAGES = 20

def parse(html):
    soup = BeautifulSoup(html, 'html.parser')
    out = []
    for card in soup.select('div[data-id][data-dates]'):
        link = card.select_one('a.listing-more-info[href*="/concert-event/"]')
        title = card.select_one('.li-shortform-title')
        venue = card.select_one('h2.li-shortform-venue a')
        if not link or not title or not venue:
            continue
        def lines(selector):
            items = card.select(selector)
            if not items:
                items = card.select(selector.replace(' .item', ''))
            return '; '.join(x.get_text(' ', strip=True) for x in items)
        performers = lines('.listing-personnel-simple .item')
        programme = lines('.listing-programme-simple .item')
        for timestamp in card['data-dates'].split(','):
            if not timestamp.strip().isdigit():
                continue
            dt = datetime.fromtimestamp(int(timestamp), LONDON)
            iso = dt.date().isoformat()
            ev = event('music', title.get_text(' ', strip=True), urljoin(URL, link['href']), 'Bachtrack',
                       etype='Classical', venue=venue.get_text(' ', strip=True), area='London',
                       start=iso, end=iso, time=dt.strftime('%H:%M'), date_text=iso,
                       subtitle=performers)
            ev.update(performers=performers, programme=programme)
            if 'playing-with-fire' in link['href'] and 'yuja-wang' in link['href']:
                continue  # Recorded avatar experience, not an in-person recital (see README).
            out.append(ev)
    return out

def fetch():
    session = requests.Session()
    session.headers['User-Agent'] = 'LondonCulture/2.0 (personal cultural listings)'
    r = session.get(URL, timeout=40)
    r.raise_for_status()
    out = parse(r.text)
    soup = BeautifulSoup(r.text, 'html.parser')
    more = soup.select_one('button.btk-search-more')
    if not out:
        raise RuntimeError('No dated concert cards; source layout may have changed')
    offset = int(more['data-startrow']) if more else 0
    params = more['data-param'] if more else ''
    for _ in range(MAX_PAGES - 1):
        if not more:
            break
        time.sleep(0.4)
        r = session.get(f'https://bachtrack.com/json/search/get-results/1280/listing/{params};startrow={offset}', timeout=40)
        r.raise_for_status()
        data = r.json().get('data', {})
        if 'count' not in data:
            raise RuntimeError('Unexpected pagination response')
        count = int(data.get('count', 0))
        if not count:
            break
        rows = parse(data.get('text', ''))
        if not rows:
            raise RuntimeError('Pagination returned no dated concert cards')
        out.extend(rows)
        offset += count
        if offset >= int(data.get('total', offset)):
            break
    else:
        raise RuntimeError('Listing exceeded pagination limit')
    return out
