"""
islandetickets.com scraper.

Scrapes the HOMEPAGE (/).

Structure found on homepage:
  - Events grouped under month headings (e.g. "Apr 2026")
  - Each event is an <a> tag linking to /event/SLUG
  - Contains: day number, h5 title, "Hosted by X @ Venue", time range, image
"""

import logging, re, sys, os, time
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup
from app.database import get_cli_session
from app.services.scraper_service import ScraperService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
logger = logging.getLogger(__name__)

BASE_URL = "https://islandetickets.com"
EVENTS_URL = BASE_URL
REQUEST_DELAY = 1.5

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

def _parse_ordinal_date(day_str: str, month_str: str, year_str: str) -> Optional[datetime]:
    try:
        day = int(re.sub(r"[^\d]", "", day_str))
        month_lower = month_str.strip().lower()[:3]
        month = MONTH_MAP.get(month_lower)
        year = int(year_str.strip())
        if day and month and year:
            return datetime(year, month, day)
        
    except (ValueError, TypeError):
        pass
    
    return None


def _parse_time_range(text: str) -> tuple[Optional[int], Optional[int]]:
    match = re.search(r"(\d{1,2}):(\d{2})(am|pm)", text.lower())
    if match:
        hour = int(match.group(1))
        
        if match.group(3) == "pm" and hour != 12:
            hour += 12
            
        return hour, 0
    
    return None, None


class IslandeTicketsScraper:
    SOURCE_NAME = "islandetickets.com"

    def __init__(self):
        try:
            import requests
            from bs4 import BeautifulSoup

        except ImportError:
            raise RuntimeError("Run: pip install requests beautifulsoup4")
        import requests as req
        self.session = req.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def _get_soup(self, url: str):
        time.sleep(REQUEST_DELAY)
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def _scrape_detail(self, url: str) -> dict:
            detail = {"description": "", "price": None, "image_url": None}
            try:
                soup = self._get_soup(url)

                img_el = soup.select_one(".event-banner img, .event-poster img, .well img, .event-details img, img[src*='rackcdn']")
                if img_el:
                    img_src = img_el.get("src")
                    
                    if img_src:
                        if img_src.startswith("//"):
                            detail["image_url"] = "https:" + img_src
                            
                        elif img_src.startswith("http"):
                            detail["image_url"] = img_src
                            
                        else:
                            path = img_src if img_src.startswith("/") else "/" + img_src
                            detail["image_url"] = BASE_URL + path

                for sel in [".event-description", ".description", ".event-details p", "div.well p"]:
                    el = soup.select_one(sel)
                    
                    if el:
                        detail["description"] = el.get_text(separator=" ", strip=True)[:2000]
                        break

                for sel in [".ticket-price", ".price", ".cost", "td.price", ".event-tickets", ".ticket-row .amount"]:
                    el = soup.select_one(sel)
                    if el:
                        text = el.get_text(strip=True).replace("$", "").replace(",", "")
                        nums = re.findall(r"\d+\.?\d*", text)
                        
                        if nums:
                            try:
                                detail["price"] = float(nums[0])
                                
                            except ValueError:
                                continue
                        break
            except Exception as e:
                logger.debug(f"Detail fetch failed {url}: {e}")
                
            return detail

    def scrape(self) -> list[dict]:
        import datetime
        records = []
        now = datetime.datetime.now()
        
        for i in range(31):
            target_date = now + datetime.timedelta(days=i)
            year = target_date.year
            month = target_date.month
            day = target_date.day
            
            api_url = f"{BASE_URL}/event_manager/calendar/events/{year}/{month}/{day}"
            logger.info(f"Fetching API: {api_url}")
            
            try:
                soup = self._get_soup(api_url)
                event_links = soup.select("a[href*='/event/']")
                
                for el in event_links:
                    href = el.get("href", "")
                    source_url = href if href.startswith("http") else BASE_URL + href
                    
                    if any(r['source_url'] == source_url for r in records):
                        continue

                    title_el = el.find("h5")
                    if title_el:
                        title = title_el.get_text(strip=True)
                        
                    else:
                        title = el.get("title") or el.get_text(strip=True) or "Unknown Event"
                    
                    full_text = el.get_text(separator=" ", strip=True)
                    venue = "TBA"
                    
                    if "@" in full_text:
                        venue = full_text.split("@")[-1].strip()

                    detail = self._scrape_detail(source_url)
                    
                    records.append({
                        "title": title,
                        "description": detail.get("description", ""),
                        "island": "Tobago" if "tobago" in venue.lower() else "Trinidad",
                        "venue": venue,
                        "date": target_date.replace(hour=0, minute=0, second=0, microsecond=0),
                        "end_date": None,
                        "price": detail.get("price"),
                        "category": "Other",
                        "source_url": source_url,
                        "image_url": detail.get("image_url"),
                    })
            except Exception as e:
                logger.error(f"Error on {api_url}: {e}")

        return records
    
    def run(self, auto_publish: bool = False) -> dict:
        records = self.scrape()
        
        with get_cli_session() as session:
            return ScraperService(session).import_from_records(records, auto_publish=auto_publish)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = IslandeTicketsScraper().run()
    print(result)