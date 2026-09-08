"""Personal, editable selection rules; never an assertion of review ratings."""
import json
import re
import unicodedata
from pathlib import Path

PREFERENCES = json.loads(Path(__file__).with_name('preferences.json').read_text(encoding='utf-8-sig'))

def folded(text):
    text = unicodedata.normalize('NFKD', str(text)).casefold()
    return re.sub(r'[^a-z0-9가-힣]+', ' ', ''.join(c for c in text if not unicodedata.combining(c))).strip()

def matches(text, names):
    haystack = ' ' + folded(text) + ' '
    return [n for n in names if (' ' + folded(n) + ' ') in haystack]

def normal_genre(value):
    key = folded(value)
    for genre, aliases in {'K-pop': ['k pop', 'kpop'], 'Rock': ['rock', 'alternative'],
                          'Pop': ['pop'], 'Metal': ['metal'], 'Hip-hop / R&B': ['hip hop', 'rap', 'r b', 'soul'],
                          'Jazz': ['jazz'], 'Electronic': ['electronic', 'dance'],
                          'Folk / Country': ['folk', 'country']}.items():
        if any(alias in key for alias in aliases):
            return genre
    return 'Other'

def classify(ev):
    ev = dict(ev)
    text = ' '.join(str(ev.get(k) or '') for k in ('title', 'subtitle', 'performers', 'programme'))
    genre = ev.get('genre') or ev.get('type', '')
    if ev.get('category') == 'exhibition':
        ev.update(collection='exhibition', genre='', featured=False, reasons=['런던 전시'])
        return ev
    if 'classical' in genre.lower() or ev.get('source') in ('Bachtrack', 'Wigmore Hall'):
        reasons = []
        if not matches(ev.get('title', ''), PREFERENCES['exclude_terms']):
            for key, label in [('classical_soloists', '주목할 연주자'), ('classical_conductors', '주목할 지휘자'), ('visiting_orchestras', '해외 오케스트라 런던 방문')]:
                names = matches(text, PREFERENCES[key])
                if names:
                    reasons.append(label + ': ' + ', '.join(names))
        ev.update(collection='classical', genre='Classical', featured=bool(reasons), reasons=reasons)
        return ev
    if ev.get('category') == 'music' and (genre.lower() == 'jazz' or ev.get('jazz_venue_listing')):
        ev.update(collection='jazz', genre='Jazz', featured=False, reasons=['재즈 클럽 프로그램 · 소울·퓨전 등 포함'] if ev.get('jazz_venue_listing') else [])
        return ev
    if ev.get('category') != 'music' or matches(ev.get('title', ''), PREFERENCES['exclude_terms']):
        return None
    artists = ev.get('artists') or []
    def artist_matches(names):
        if artists:
            return [n for n in names if any(folded(n) == folded(a) for a in artists)]
        return matches(ev.get('title', ''), [n for n in names if len(folded(n)) > 3 and folded(n) not in ('dean', 'rose', 'lisa', 'shinee')])
    korean = artist_matches(PREFERENCES['korean_artists'])
    famous = artist_matches(PREFERENCES['headline_artists'])
    kpop = any(folded(g) in ('k pop', 'kpop') for g in (ev.get('genres') or [genre]))
    if not korean and not famous and not kpop:
        if ev.get('discovery'):
            ev.update(collection='discovery', genre=normal_genre(genre), featured=False, reasons=[])
            return ev
        return None
    ev.update(collection='korean' if korean or kpop else 'headliners',
              genre=('K-pop' if kpop or any(n in PREFERENCES['korean_pop_artists'] for n in korean) else normal_genre(genre)), featured=False,
              reasons=[('한국 아티스트 관심 목록: ' + ', '.join(korean)) if korean else
                       'K-pop 장르로 분류된 공연' if kpop else '유명 아티스트 관심 목록: ' + ', '.join(famous)])
    return ev
