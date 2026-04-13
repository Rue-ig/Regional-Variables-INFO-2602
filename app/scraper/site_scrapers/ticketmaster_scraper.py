import logging, sys, os, time, requests
from datetime import datetime
from typing import Optional
from app.config import get_settings
from app.database import get_cli_session
from app.services.scraper_service import ScraperService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
logger = logging.getLogger(__name__)

BASE_URL = "https://app.ticketmaster.com/discovery/v2"

GLOBAL_KEYWORDS = [
    "Soca", "Dancehall", "Reggae", "Calypso", 
    "Trinidad Carnival", "Barbados Crop Over", "Sumfest"
]

class TicketmasterScraper:
    SOURCE_NAME = "Ticketmaster"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_settings().ticketmaster_api_key
        
        if not self.api_key:
            raise ValueError("TICKETMASTER_API_KEY not found in .env")
            
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "CaribbeanEventsBot/1.0"})

    def _infer_island(self, event: dict) -> str:
        venues = (event.get("_embedded") or {}).get("venues") or []
        venue = venues[0] if venues else {}
        
        city = (venue.get("city") or {}).get("name", "").lower()
        country = (venue.get("country") or {}).get("name", "").lower()
        title = event.get("name", "").lower()
        desc = (event.get("info") or "").lower()
        
        full_text = f"{title} {city} {country} {desc}"
                
        mapping = {
            "Trinidad": ["trinidad", "port of spain", "tt"],
            "Tobago": ["tobago", "scarborough"],
            "Barbados": ["barbados", "bridgetown", "crop over", "bb"],
            "Jamaica": ["jamaica", "kingston", "montego bay", "sumfest", "jm"],
            "Antigua": ["antigua", "st. john", "ag"],
            "St. Lucia": ["st. lucia", "saint lucia", "castries", "lucian", "lc"],
            "Grenada": ["grenada", "st. george", "carriacou", "gd"],
            "St. Kitts": ["st. kitts", "nevis", "basseterre", "kn"],
            "Cayman Islands": ["cayman", "george town", "ky"],
            "Aruba": ["aruba", "oranjestad", "aw"],
            "Dominica": ["dominica", "roseau", "dm"],
            "St. Vincent": ["st. vincent", "vincy", "vc"],
            "Bahamas": ["bahamas", "nassau", "bs"]
        }

        for island_name, keywords in mapping.items():
            if any(kw in full_text for kw in keywords):
                return island_name
        
        return "Other"

    def scrape(self) -> list[dict]:
        all_records = []
        seen_urls = set()

        for kw in GLOBAL_KEYWORDS:
            logger.info(f"Ticketmaster: Searching for '{kw}'...")
            params = {
                "apikey": self.api_key,
                "keyword": kw,
                "size": 100,
                "sort": "date,asc"
            }
            
            try:
                time.sleep(0.5) # Avoid rate limits
                resp = self.session.get(f"{BASE_URL}/events.json", params=params, timeout=15)
                
                if not resp.ok:
                    continue
                
                data = resp.json()
                events = (data.get("_embedded") or {}).get("events") or []
                
                for ev in events:
                    url = ev.get("url")
                    
                    if not url or url in seen_urls:
                        continue
                    
                    dates = ev.get("dates", {}).get("start", {})
                    date_str = dates.get("dateTime") or dates.get("localDate")
                    if not date_str:
                        continue

                    category = "Music"
                    
                    all_records.append({
                        "title": ev.get("name"),
                        "description": (ev.get("info") or ev.get("pleaseNote") or "")[:1000],
                        "island": self._infer_island(ev),
                        "venue": ((ev.get("_embedded") or {}).get("venues") or [{}])[0].get("name", "TBA"),
                        "date": datetime.fromisoformat(date_str.replace("Z", "")),
                        "end_date": None,
                        "price": None,
                        "category": category,
                        "source_url": url,
                        "image_url": (ev.get("images") or [{}])[0].get("url"),
                    })
                    
                    seen_urls.add(url)
                    
            except Exception as e:
                logger.error(f"TM search error for {kw}: {e}")

        logger.info(f"Ticketmaster total: {len(all_records)} unique events found.")
        
        return all_records

    def run(self, auto_publish: bool = False) -> dict:
        records = self.scrape()
        with get_cli_session() as session:
            return ScraperService(session).import_from_records(records, auto_publish=auto_publish)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(TicketmasterScraper().run())