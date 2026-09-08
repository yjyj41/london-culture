"""Refresh explicitly registered DICE event URLs using public MusicEvent metadata."""
import json
import re
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from normalize import event
from curation import classify

CONFIG = Path(__file__).resolve().parents[1] / 'extra_sources.json'

def nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from nodes(item)
    elif isinstance(value, dict):
        yield value
        yield from nodes(value.get('@graph', []))

def parse(html, config):
    for script in BeautifulSoup(html, 'html.parser').select('script[type="application/ld+json"]'):
        try:
            values = json.loads(script.string or script.get_text())
        except ValueError:
            continue
        for raw in nodes(values):
            types = raw.get('@type', [])
            if 'MusicEvent' not in ([types] if isinstance(types, str) else types):
                continue
            if raw.get('eventStatus', '').rsplit('/', 1)[-1] in ('EventCancelled', 'EventPostponed'):
                return None
            location = raw.get('location') or {}
            address = location.get('address') or {}
            if address.get('addressLocality', '').casefold() != 'london':
                return None
            start = datetime.fromisoformat(raw['startDate'].replace('Z', '+00:00'))
            end = datetime.fromisoformat((raw.get('endDate') or raw['startDate']).replace('Z', '+00:00'))
            if start.tzinfo is None or end.tzinfo is None:
                raise ValueError('DICE time zone missing')
            start, end = start.astimezone(ZoneInfo('Europe/London')), end.astimezone(ZoneInfo('Europe/London'))
            # Overnight gigs are one performance on their start date.
            ev = event('music', raw['name'], config['url'], 'DICE',
                       etype=config.get('genre', 'Other'), venue=location.get('name', ''),
                       subtitle=config.get('subtitle', ''), area='London',
                       start=start.date().isoformat(), end=start.date().isoformat(), time=start.strftime('%H:%M'))
            performers = raw.get('performer') or []
            if isinstance(performers, dict):
                performers = [performers]
            ev['artists'] = list(dict.fromkeys(config.get('artists', []) + [p['name'] for p in performers if p.get('name')]))
            return classify(ev)
    raise ValueError('DICE MusicEvent metadata missing')

def parse_earth(html, config):
    soup = BeautifulSoup(html, 'html.parser')
    card = soup.select_one('article.event')
    if card is None:
        raise ValueError('Official venue event missing')
    title = card.select_one('h1[itemprop="name"]')
    day = card.select_one('time[itemprop="startDate"][datetime]')
    clock = card.select_one('.event__times')
    if title is None or day is None or clock is None:
        raise ValueError('Official venue dates missing')
    title = title.get_text(' ', strip=True)
    if re.search(r'cancelled|postponed', title, re.I):
        return None
    date = datetime.fromisoformat(day['datetime']).date().isoformat()
    match = re.search(r'\b\d{1,2}:\d{2}\b', clock.get_text())
    if not match:
        raise ValueError('Official venue time missing')
    ev = event('music', title, config['url'], 'DICE', etype=config.get('genre', 'Other'),
               venue='EartH Theatre' if 'event-venue-earth-theatre' in card.get('class', []) else 'EartH',
               area='London', start=date, end=date, time=match[0], subtitle=config.get('subtitle', ''))
    ev.update(artists=config.get('artists', []), verification_source='EartH', verification_url=config['evidence_url'])
    return classify(ev)

def fetch():
    configs = json.loads(CONFIG.read_text(encoding='utf-8'))['dice_events']
    out = []
    for config in configs:
        url = urlparse(config['url'])
        if url.scheme != 'https' or url.netloc != 'dice.fm' or not url.path.startswith('/event/'):
            raise ValueError('Use a full https://dice.fm/event/ link')
        try:
            r = requests.get(config['url'], timeout=35)
            r.raise_for_status()
            ev = parse(r.text, config)
        except (requests.RequestException, ValueError):
            evidence = urlparse(config.get('evidence_url', ''))
            if evidence.scheme != 'https' or evidence.netloc != 'earthackney.co.uk' or not evidence.path.startswith('/events/'):
                raise
            try:
                r = requests.get(config['evidence_url'], timeout=35)
                r.raise_for_status()
                ev = parse_earth(r.text, config)
            except (requests.RequestException, ValueError):
                saved = config.get('verified_event')
                if not saved:
                    raise
                datetime.strptime(saved['start'], '%Y-%m-%d')
                datetime.strptime(saved['time'], '%H:%M')
                datetime.fromisoformat(saved['verified_at'])
                ev = event('music', saved['title'], config['url'], 'DICE',
                           etype=config.get('genre', 'Other'), venue=saved['venue'], area='London',
                           start=saved['start'], end=saved['start'], time=saved['time'], subtitle=config.get('subtitle', ''))
                ev.update(artists=config.get('artists', []), verification_mode='manual', verified_at=saved['verified_at'])
                ev = classify(ev)
        if ev:
            out.append(ev)
    return out
