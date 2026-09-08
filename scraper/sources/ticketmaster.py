"""Search watched artists individually so distant major concerts are not lost."""
import os
import time
import requests
from normalize import event
from curation import PREFERENCES, classify

API = 'https://app.ticketmaster.com/discovery/v2/events.json'

def parse(ev):
    if (ev.get('dates') or {}).get('status', {}).get('code') in ('cancelled', 'postponed'):
        return None
    embedded = ev.get('_embedded') or {}
    venues = embedded.get('venues') or [{}]
    cls = (ev.get('classifications') or [{}])[0]
    genres = [(cls.get(k) or {}).get('name', '') for k in ('genre', 'subGenre')]
    genre = next((g for g in reversed(genres) if g not in ('', 'Undefined')), 'Other')
    dates = (ev.get('dates') or {}).get('start', {})
    if dates.get('dateTBA') or dates.get('dateTBD') or not dates.get('localDate'):
        return None
    prices = ev.get('priceRanges') or []
    price = ''
    if prices and prices[0].get('min') is not None:
        symbol = '£' if prices[0].get('currency') == 'GBP' else prices[0].get('currency', '')
        price = f"{symbol}{prices[0]['min']:g}부터"
    result = event('music', ev.get('name', ''), ev.get('url', ''), 'Ticketmaster',
                   etype=genre, venue=venues[0].get('name', ''), area='London',
                   start=dates['localDate'], end=dates['localDate'],
                   time='' if dates.get('timeTBA') else (dates.get('localTime') or '')[:5],
                   price=price)
    result.update(artists=[a.get('name', '') for a in embedded.get('attractions', [])],
                  genres=genres, genre=genre)
    return classify(result)

def fetch():
    key = os.environ.get('TICKETMASTER_API_KEY')
    if not key:
        raise RuntimeError('TICKETMASTER_API_KEY is not configured')
    queries = [{'keyword': n} for n in dict.fromkeys(PREFERENCES['headline_artists'] + PREFERENCES['korean_artists'])]
    queries.append({'classificationName': 'K-Pop'})
    out, seen = [], set()
    for query in queries:
        for page in range(5):
            params = dict(apikey=key, city='London', countryCode='GB', segmentName='Music',
                          sort='date,asc', size=200, page=page,
                          startDateTime=time.strftime('%Y-%m-%dT00:00:00Z'), **query)
            # Do not log exception URLs: they contain the API key.
            try:
                r = requests.get(API, params=params, timeout=30)
                r.raise_for_status()
                data = r.json()
            except Exception:
                raise RuntimeError('Ticketmaster request failed; check API availability and quota') from None
            for raw in (data.get('_embedded') or {}).get('events', []):
                if raw.get('id') in seen:
                    continue
                seen.add(raw.get('id'))
                ev = parse(raw)
                if ev:
                    out.append(ev)
            time.sleep(0.25)
            if page + 1 >= (data.get('page') or {}).get('totalPages', 1):
                break
        else:
            raise RuntimeError('Ticketmaster query exceeded pagination limit')
    return out

