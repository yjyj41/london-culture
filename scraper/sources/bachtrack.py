"""
Bachtrack — classical concerts / opera / dance in London.

Bachtrack has NO public API and the listing is rendered with JavaScript,
so we drive a headless browser (Playwright). The site's DOM class names can
change; if Bachtrack stops returning results, adjust ROW_SELECTOR / the field
selectors below — that is the only part that needs tuning.

Returns [] gracefully on any error so it never breaks the build.
"""
import re
from normalize import event, parse_date_range

URL = 'https://bachtrack.com/search-events/city=london'

# --- selectors to tune if the layout changes -------------------------------
ROW_SELECTOR = 'a[href*="/performance"], a[href*="/event"]'
# ---------------------------------------------------------------------------

DATE_RE = re.compile(r'\d{1,2}\s+[A-Z][a-z]+\s+\d{4}')


def fetch():
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        print('  [bachtrack] playwright not installed - skipping')
        return []

    out, seen = [], set()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent='Mozilla/5.0 (X11; Linux x86_64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/124.0 Safari/537.36')
            page.goto(URL, wait_until='networkidle', timeout=45000)
            page.wait_for_timeout(2500)

            rows = page.query_selector_all(ROW_SELECTOR)
            for row in rows:
                href = row.get_attribute('href') or ''
                if not href or href in seen:
                    continue
                title = (row.inner_text() or '').strip().split('\n')[0]
                if not title or len(title) < 3:
                    continue
                # look at the surrounding card for a date + venue
                ctx = ''
                try:
                    parent = row.evaluate_handle('e => e.closest("li,article,div")')
                    ctx = parent.as_element().inner_text() if parent else ''
                except Exception:
                    ctx = row.inner_text()
                dm = DATE_RE.search(ctx or '')
                date_text = dm.group(0) if dm else ''
                lines = [l.strip() for l in (ctx or '').split('\n') if l.strip()]
                venue = ''
                for l in lines:
                    if l != title and not DATE_RE.search(l):
                        venue = l
                        break
                url = href if href.startswith('http') else 'https://bachtrack.com' + href
                seen.add(href)
                out.append(event('music', title, url, 'Bachtrack',
                                 etype='Classical', venue=venue, area='London',
                                 date_text=date_text))
            browser.close()
    except Exception as e:
        print(f'  [bachtrack] error: {e}')
        return out

    print(f'  [bachtrack] {len(out)} events')
    return out
