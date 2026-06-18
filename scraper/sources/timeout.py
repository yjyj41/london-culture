"""
Time Out London — broad "what's on" (theatre / art / events).

Time Out is editorial and sits behind Cloudflare, so this is a best-effort
Playwright scraper. It often works locally but may be blocked in CI; it is
DISABLED by default. Set ENABLED = True to try it.

Returns [] gracefully on any error.
"""
import re
from normalize import event

ENABLED = False  # flip to True to attempt Time Out scraping

URL = 'https://www.timeout.com/london/theatre/best-theatre-in-london'
CARD_SELECTOR = 'article a[href*="/london/"]'
DATE_RE = re.compile(r'\d{1,2}\s+[A-Z][a-z]+\s+\d{4}')


def fetch():
    if not ENABLED:
        print('  [timeout] disabled (set ENABLED=True to try)')
        return []
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print('  [timeout] playwright not installed - skipping')
        return []

    out, seen = [], set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(URL, wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(2500)
            for a in page.query_selector_all(CARD_SELECTOR):
                href = a.get_attribute('href') or ''
                title = (a.inner_text() or '').strip().split('\n')[0]
                if not href or not title or len(title) < 4 or href in seen:
                    continue
                seen.add(href)
                url = href if href.startswith('http') else 'https://www.timeout.com' + href
                out.append(event('event', title, url, 'Time Out',
                                 etype='Editorial pick', venue='', area='London'))
            browser.close()
    except Exception as e:
        print(f'  [timeout] error: {e}')
        return out

    print(f'  [timeout] {len(out)} events')
    return out
