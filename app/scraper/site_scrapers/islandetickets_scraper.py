"""
islandetickets.com scraper.
"""
import logging, re, time, requests
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup, Tag
from app.database import get_cli_session
from app.services.scraper_service import ScraperService

logger = logging.getLogger(__name__)

BASE_URL      = "https://islandetickets.com"
HOMEPAGE_URL  = BASE_URL + "/"
REQUEST_DELAY = 1.5

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,  "may": 5,  "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

def _parse_month_heading(text: str) -> tuple[Optional[int], Optional[int]]:
    """Parse 'Apr 2026' or 'Apr2026' → (month, year)."""
    m = re.search(r"([A-Za-z]+)\s*(\d{4})", text)
    if m:
        month = MONTH_MAP.get(m.group(1).lower()[:3])
        year  = int(m.group(2))
        return month, year
    return None, None

def _parse_day_ordinal(text: str) -> Optional[int]:
    """Parse '17th' → 17."""
    m = re.search(r"(\d+)", text)
    return int(m.group(1)) if m else None

def _detect_island(venue_text: str) -> str:
    lower = venue_text.lower()
    if "tobago"   in lower: return "Tobago"
    if "bahamas"  in lower: return "Bahamas"
    if "barbados" in lower: return "Barbados"
    if "jamaica"  in lower: return "Jamaica"
    if "st. lucia" in lower or "saint lucia" in lower: return "St. Lucia"
    if "grenada"  in lower: return "Grenada"
    if "antigua"  in lower: return "Antigua"
    return "Trinidad"

class IslandeTicketsScraper:
    SOURCE_NAME = "islandetickets.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def _get_soup(self, url: str) -> BeautifulSoup:
        time.sleep(REQUEST_DELAY)
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def scrape(self) -> list[dict]:
        soup = self._get_soup(HOMEPAGE_URL)
        records   = []
        seen_urls = set()

        current_month: Optional[int] = None
        current_year:  Optional[int] = None

        for tag in soup.find_all(True):
            if not isinstance(tag, Tag):
                continue

            if tag.name == "h5" and "event-list-month" in tag.get("class", []):
                current_month, current_year = _parse_month_heading(tag.get_text())
                continue

            if tag.name == "a" and "event-list-item" in tag.get("class", []):
                if current_month is None or current_year is None:
                    continue

                href = tag.get("href", "")
                source_url = href if href.startswith("http") else BASE_URL + href
                if source_url in seen_urls:
                    continue
                seen_urls.add(source_url)

                day_el  = tag.select_one(".col-sm-1 div")
                day_num = _parse_day_ordinal(day_el.get_text() if day_el else "")
                if not day_num:
                    continue

                try:
                    date = datetime(current_year, current_month, day_num)
                except ValueError:
                    continue

                title_el = tag.select_one("h5.mt-0")
                title    = title_el.get_text(strip=True) if title_el else tag.get_text(strip=True)[:80]
                if not title:
                    continue
                  
                secondary = tag.select_one(".secondary")
                sec_text  = secondary.get_text(separator="\n", strip=True) if secondary else ""
                venue     = "TBA"
                for line in sec_text.splitlines():
                    if line.startswith("@"):
                        venue = line[1:].strip()
                        break

                img = tag.find("img")
                image_url = None
                if img:
                    src = img.get("src", "")
                    if src.startswith("//"):
                        image_url = "https:" + src
                    elif src.startswith("http"):
                        image_url = src

                records.append({
                    "title":       title,
                    "description": "",
                    "island":      _detect_island(venue),
                    "venue":       venue,
                    "date":        date,
                    "end_date":    None,
                    "price":       None,
                    "category":    "Other",
                    "source_url":  source_url,
                    "image_url":   image_url,
                })

        logger.info(f"IslandETickets: {len(records)} events scraped")
        return records

    def run(self, auto_publish: bool = False) -> dict:
        records = self.scrape()
        with get_cli_session() as session:
            return ScraperService(session).import_from_records(records, auto_publish=auto_publish)
