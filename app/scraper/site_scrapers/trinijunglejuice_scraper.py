"""
trinijunglejuice.com/events scraper — uses Playwright (required, site is a React SPA).
Playwright renders the JavaScript and gives us the real DOM.

"""

import logging, re, sys, os
from datetime import datetime
from typing import Optional
from app.database import get_cli_session
from app.services.scraper_service import ScraperService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
logger = logging.getLogger(__name__)

EVENTS_URL = "https://trinijunglejuice.com/events"
REQUEST_DELAY = 2.0


def _parse_date(text: str) -> Optional[datetime]:
    text = text.strip()
    
    for fmt in [
        "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y",
        "%A, %B %d, %Y", "%A, %b %d, %Y",
        "%B %d, %Y %I:%M %p", "%b %d, %Y %I:%M %p",
        "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S",
    ]:
        try:
            return datetime.strptime(text, fmt)
        
        except ValueError:
            continue
        
    return None


def _detect_island(text: str) -> str:
    lower = text.lower()
    for kw, island in {
        "tobago": "Tobago", "trinidad": "Trinidad",
        "barbados": "Barbados", "jamaica": "Jamaica",
        "st. lucia": "St. Lucia", "saint lucia": "St. Lucia",
        "grenada": "Grenada", "antigua": "Antigua",
        "bahamas": "Bahamas", "puerto rico": "Puerto Rico",
        "martinique": "Martinique", "guadeloupe": "Guadeloupe",
    }.items():
        if kw in lower:
            return island
        
    return "Trinidad"


class TJJScraper:
    SOURCE_NAME = "trinijunglejuice.com"

    def scrape(self) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright
            
        except ImportError:
            raise RuntimeError(
                "Playwright not installed or browsers not set up.\n"
                "Run: pip install playwright\n"
                "Then: playwright install chromium"
            )

        records = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            logger.info(f"Loading {EVENTS_URL}")
            page.goto(EVENTS_URL, wait_until="networkidle", timeout=30000)

            try:
                page.wait_for_selector(
                    "a[href*='/events/'], .event-card, article, [class*='event']",
                    timeout=15000
                )
                
            except Exception:
                logger.warning("Timed out waiting for event cards — trying to parse anyway")

            for _ in range(5):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                page.wait_for_timeout(800)

            content = page.content()
            browser.close()

        try:
            from bs4 import BeautifulSoup
            
        except ImportError:
            raise RuntimeError("Run: pip install beautifulsoup4")

        soup = BeautifulSoup(content, "html.parser")

        cards = (
            soup.select("a[href*='/events/']") or
            soup.select("[class*='EventCard'], [class*='event-card'], [class*='eventCard']") or
            soup.select("article") or
            []
        )

        if not cards:
            logger.warning("No event cards found on TJJ — inspect the rendered HTML and update selectors")
            return []

        for card in cards:
            try:
                title_el = card.select_one("h2, h3, h4, [class*='title'], [class*='Title']")
                title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:80]
                if not title:
                    continue

                # Date
                date = None
                date_el = card.select_one("time, [class*='date'], [class*='Date']")
                if date_el:
                    dt_attr = date_el.get("datetime", "")
                    if dt_attr:
                        try:
                            date = datetime.fromisoformat(dt_attr)
                            
                        except ValueError:
                            date = _parse_date(date_el.get_text(strip=True))
                    else:
                        date = _parse_date(date_el.get_text(strip=True))

                if not date:
                    full_text = card.get_text(separator=" ")
                    date_patterns = [
                        r"([A-Za-z]+ \d{1,2},? \d{4})",
                        r"(\d{1,2} [A-Za-z]+ \d{4})",
                    ]
                    
                    for pattern in date_patterns:
                        m = re.search(pattern, full_text)
                        if m:
                            date = _parse_date(m.group(1))
                            if date:
                                break

                if not date:
                    continue

                href = card.get("href", "") if card.name == "a" else ""
                if not href:
                    link_el = card.find("a")
                    href = link_el.get("href", "") if link_el else ""
                source_url = (href if href.startswith("http") else "https://trinijunglejuice.com" + href) if href else None

                venue_el = card.select_one("[class*='venue'], [class*='location'], [class*='Venue']")
                venue = venue_el.get_text(strip=True) if venue_el else "TBA"

                island = _detect_island(card.get_text())

                img = card.find("img")
                image_url = None
                if img:
                    image_url = img.get("src") or img.get("data-src")

                records.append({
                    "title": title,
                    "description": "",
                    "island": island,
                    "venue": venue,
                    "date": date,
                    "end_date": None,
                    "price": None,
                    "category": "Other",
                    "source_url": source_url,
                    "image_url": image_url,
                })
                
            except Exception as e:
                logger.debug(f"TJJ: skipping card: {e}")

        logger.info(f"TJJ: scraped {len(records)} events")
        
        return records

    def run(self, auto_publish: bool = False) -> dict:
        records = self.scrape()
        with get_cli_session() as session:
            return ScraperService(session).import_from_records(records, auto_publish=auto_publish)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = TJJScraper().run()
    print(result)