"""Shared helpers: date parsing + event normalisation."""
import re
import hashlib
from datetime import datetime

MONTHS = {
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9, 'oct': 10,
    'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
}

# normalise the various dash characters used in date ranges
DASHES = ['–', '—', '‒', '‑', '‐', '−']


def _clean(s: str) -> str:
    s = s or ''
    for d in DASHES:
        s = s.replace(d, '-')
    return re.sub(r'\s+', ' ', s).strip()


def _parse_one(token: str, fallback_year=None):
    """Parse 'd Month YYYY' / 'Month YYYY' / 'd Month' -> (datetime|None, year)."""
    token = _clean(token)
    m = re.search(r'(\d{1,2})?\s*([A-Za-z]+)\s*(\d{4})?', token)
    if not m:
        return None, fallback_year
    day = int(m.group(1)) if m.group(1) else 1
    mon = MONTHS.get((m.group(2) or '').lower())
    if not mon:
        return None, fallback_year
    year = int(m.group(3)) if m.group(3) else fallback_year
    if not year:
        return None, fallback_year
    try:
        return datetime(year, mon, day), year
    except ValueError:
        return None, year


def parse_date_range(text: str):
    """
    Turn human date strings into (start_iso, end_iso, raw).
    Handles: 'Until 23 August 2026', '2 July - 20 September 2026',
             '25 Jun 2026 - 3 Jan 2027', '11 June 2026', '2026'.
    """
    raw = (text or '').strip()
    t = _clean(text)
    if not t:
        return None, None, raw

    # "Until <date>" -> open start, end = date
    m = re.match(r'(?:until|to|ends?)\s+(.+)', t, re.I)
    if m:
        end, _ = _parse_one(m.group(1))
        return None, (end.strftime('%Y-%m-%d') if end else None), raw

    # range "A - B"
    if '-' in t:
        left, right = [p.strip() for p in t.split('-', 1)]
        end, yr = _parse_one(right)
        start, _ = _parse_one(left, fallback_year=yr)
        return (start.strftime('%Y-%m-%d') if start else None,
                end.strftime('%Y-%m-%d') if end else None, raw)

    # bare year
    if re.fullmatch(r'\d{4}', t):
        return f'{t}-01-01', f'{t}-12-31', raw

    # single date
    single, _ = _parse_one(t)
    if single:
        iso = single.strftime('%Y-%m-%d')
        return iso, iso, raw

    return None, None, raw


def make_id(*parts) -> str:
    return hashlib.md5('|'.join(str(p) for p in parts).encode()).hexdigest()[:12]


def event(category, title, url, source, *, subtitle='', etype='', venue='',
          area='', date_text='', start=None, end=None, price=''):
    """Build one normalised event dict."""
    if (start is None or end is None) and date_text:
        s, e, _ = parse_date_range(date_text)
        start = start or s
        end = end or e
    return {
        'id': make_id(source, title, venue, start or date_text),
        'category': category,
        'title': _clean(title),
        'subtitle': _clean(subtitle),
        'type': _clean(etype),
        'venue': _clean(venue),
        'area': _clean(area),
        'date_text': _clean(date_text),
        'start': start,
        'end': end,
        'price': _clean(price),
        'url': url,
        'source': source,
    }
