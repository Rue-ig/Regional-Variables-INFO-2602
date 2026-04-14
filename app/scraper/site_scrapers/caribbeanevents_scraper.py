"""
caribbeanevents.com scraper.
"""
import logging, re, sys, os, time
from datetime import datetime
from typing import Optional
import requests
from bs4 import BeautifulSoup
from app.database import get_cli_session
from app.services.scraper_service import ScraperService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
logger = logging.getLogger(__name__)

BASE_URL = "https://caribbeanevents.com"
REQUEST_DELAY = 1.0

VALID_CATEGORIES = [
    'Music', 'Food & Drink', 'Sports', 'Culture & Arts', 
    'Nightlife', 'Festival', 'Carnival', 'Business', 'Other'
]

def _detect_category(text: str) -> str:
    text = text.lower()
    
    if any(word in text for word in ['concert', 'music', 'reggae', 'soca', 'dj', 'party']):
        return 'Music'
    
    if any(word in text for word in ['food', 'drink', 'dining', 'culinary', 'festival']):
        return 'Festival'
    
    if any(word in text for word in ['carnival', 'mas', 'jouver']):
        return 'Carnival'
    
    if any(word in text for word in ['sport', 'cricket', 'football', 'race', 'marathon']):
        return 'Sports'
    
    return 'Other'
    
def _detect_island(text: str) -> str:
    text = text.lower().replace("-", " ")
    mapping = {
        "port of spain":  "Trinidad",
        "chaguaramas":    "Trinidad",
        "san fernando":   "Trinidad",
        "scarborough":    "Tobago",
        "pigeon point":   "Tobago",
        "bridgetown":     "Barbados",
        "kingston":       "Jamaica",
        "montego":        "Jamaica",
        "nassau":         "Bahamas",
        "georgetown":     "Guyana",
        "tobago":         "Tobago",
        "trinidad":       "Trinidad",
        "barbados":       "Barbados",
        "jamaica":        "Jamaica",
        "antigua":        "Antigua",
        "saint lucia":    "St. Lucia",
        "st. lucia":      "St. Lucia",
        "grenada":        "Grenada",
        "st. vincent":    "St. Vincent",
        "dominica":       "Dominica",
        "bahamas":        "Bahamas",
        "cayman":         "Cayman Islands",
        "puerto rico":    "Puerto Rico",
        "martinique":     "Martinique",
        "guadeloupe":     "Guadeloupe",
        "curacao":        "Curaçao",
        "curaçao":        "Curaçao",
        "aruba":          "Aruba",
        "guyana":         "Guyana",
    }
    
    for kw, island in mapping.items():
        if kw in text:
            return island
            
    return "Other"

class CaribbeanEventsScraper:
    SOURCE_NAME = "caribbeanevents.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        })

    def _get_soup(self, url: str):
        time.sleep(REQUEST_DELAY)
        
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            
            return BeautifulSoup(resp.text, "html.parser")
        
        except Exception as e:
            logger.debug(f"Request failed for {url}: {e}")
            
            return None

    def _get_event_urls(self) -> list[str]:
        urls = set()
        
        api_url = f"{BASE_URL}/wp-json/wp/v2/posts?categories=event&per_page=20"
        try:
            logger.info("Fetching via WP-JSON API...")
            resp = self.session.get(api_url, timeout=10)
            if resp.status_code == 200:
                for item in resp.json():
                    if item.get('link'): urls.add(item.get('link'))
        except:
            pass

        if not urls:
            logger.info("API failed. Scanning /event/ page...")
            soup = self._get_soup(f"{BASE_URL}/event/")
            if soup:
                for a in soup.find_all("a", href=True):
                    href = a['href']
                    if "/event/" in href and not any(x in href for x in ["/page/", "category", "tag"]):
                        if href.rstrip("/") != f"{BASE_URL}/event":
                            urls.add(href)

        return list(urls)

    def _scrape_event_page(self, url: str) -> Optional[dict]:
            soup = self._get_soup(url)
            if not soup: return None

            try:
                title_el = soup.select_one("h1.entry-title, .cbp-l-project-title, h1")
                if not title_el:
                    return None
                title = title_el.get_text(strip=True)

                content_el = soup.select_one(".cbp-l-project-desc, .entry-content, article")
                content_text = content_el.get_text(separator=" ", strip=True) if content_el else ""

                date = None
                date_match = re.search(r"(\w+ \d{1,2}(?:st|nd|rd|th)?,?\s*\d{4})", content_text)
                if date_match:
                    raw = re.sub(r"(st|nd|rd|th)", "", date_match.group(1)).replace(",", "")
                    for fmt in ["%B %d %Y", "%d %B %Y", "%b %d %Y"]:
                        try:
                            date = datetime.strptime(raw, fmt)
                            break
                            
                        except:
                            continue

                venue = "TBA"
                venue_match = re.search(r"(?:Venue|Location|Held at)[:\s]+([^\n\.]{3,50})", content_text, re.I)
                if venue_match:
                    venue = venue_match.group(1).strip()

                img = soup.select_one(".cbp-l-project-img img, img.wp-post-image, .entry-content img, .post-thumbnail img")
                image_url = None
                if img:
                    image_url = img.get("data-src") or img.get("src") or img.get("data-lazy-src") or img.get("srcset")
                    
                    if image_url and "," in image_url:
                        image_url = image_url.split(",")[0].split(" ")[0]
                    
                    if image_url and not image_url.startswith("http"):
                        image_url = BASE_URL + image_url

                category = _detect_category(title + " " + content_text)

                return {
                    "title": title,
                    "description": content_text[:1000],
                    "island": _detect_island(title + " " + content_text + " " + venue),
                    "venue": venue,
                    "date": date or datetime.now(),
                    "end_date": None,
                    "price": None,
                    "category": category,
                    "source_url": url,
                    "image_url": image_url,
                }
                
            except Exception as e:
                logger.error(f"Error on {url}: {e}")
                
                return None

    def scrape(self) -> list[dict]:
        soup = self._get_soup(f"{BASE_URL}/")
        if not soup:
            return []
    
        records   = []
        seen_urls = set()
    
        for item in soup.select(".ovaem_slider_events_two .item, .ovaem_list_events_one .item"):
            try:
                link_el    = item.select_one("a[href*='/event/']")
                if not link_el:
                    continue
                source_url = link_el.get("href", "")
                if source_url in seen_urls:
                    continue
                seen_urls.add(source_url)
    
                title_el = item.select_one("h2.title a, h2.title")
                title    = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue
                    
                countdown = item.select_one("[data-day][data-month][data-year]")
                date: Optional[datetime] = None
                if countdown:
                    try:
                        date = datetime(
                            int(countdown["data-year"]),
                            int(countdown["data-month"]),
                            int(countdown["data-day"]),
                        )
                    except (ValueError, KeyError):
                        pass
    
                if not date:
                    time_el = item.select_one(".time")
                    if time_el:
                        raw = time_el.get_text(strip=True)
                        for fmt in ["%B %d, %Y", "%b %d, %Y", "%B %d %Y"]:
                            try:
                                date = datetime.strptime(raw, fmt)
                                break
                                
                            except ValueError:
                                continue
    
                if not date:
                    continue
    
                venue_el = item.select_one(".venue")
                venue    = venue_el.get_text(strip=True) if venue_el else "TBA"
    
                desc_el  = item.select_one(".desc")
                desc     = desc_el.get_text(strip=True) if desc_el else ""
    
                image_url = None
                wrap_img  = item.select_one(".wrap_img")
                if wrap_img:
                    style = wrap_img.get("style", "")
                    m = re.search(r"url\(['\"]?(https?://[^'\")\s]+)['\"]?\)", style)
                    
                    if m:
                        image_url = m.group(1)
    
                full_text = title + " " + desc
                records.append({
                    "title":       title,
                    "description": desc[:1000],
                    "island": _detect_island(full_text + " " + venue),
                    "venue":       venue,
                    "date":        date,
                    "end_date":    None,
                    "price":       None,
                    "category":   _detect_category(full_text),
                    "source_url":  source_url,
                    "image_url":   image_url,
                })
    
            except Exception as ex:
                logger.debug(f"caribbeanevents: skipping card: {ex}")
    
        logger.info(f"caribbeanevents.com: {len(records)} events scraped")
        return records

    def run(self, auto_publish: bool = False) -> dict:
        records = self.scrape()
        
        with get_cli_session() as session:
            return ScraperService(session).import_from_records(records, auto_publish=auto_publish)
