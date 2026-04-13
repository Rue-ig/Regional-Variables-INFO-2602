import logging, sys, os, time, re, requests as req
from datetime import datetime
from typing import Optional
from app.models.event import Island, EventCategory
from app.database import get_cli_session
from app.services.scraper_service import ScraperService

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
logger = logging.getLogger(__name__)

LOCATIONS = [
    {"name": "Trinidad",           "slug": "trinidad-and-tobago"},
    {"name": "Barbados",           "slug": "barbados"},
    {"name": "Jamaica",            "slug": "jamaica"},
    {"name": "St. Lucia",          "slug": "saint-lucia"},
    {"name": "Grenada",            "slug": "grenada"},
    {"name": "Antigua",            "slug": "antigua-and-barbuda"},
    {"name": "Dominican Republic", "slug": "dominican-republic"},
    {"name": "Puerto Rico",        "slug": "puerto-rico"},
    {"name": "The Bahamas",        "slug": "the-bahamas"},
    {"name": "Guyana",             "slug": "guyana"},
    {"name": "Suriname",           "slug": "suriname"},
    {"name": "Cayman Islands",     "slug": "united-kingdom--cayman-islands"},
    {"name": "US Virgin Islands",  "slug": "united-states--saint-thomas"},
    {"name": "British Virgin Is.", "slug": "united-kingdom--british-virgin-islands"},
    {"name": "Curaçao",            "slug": "curacao"},
    {"name": "Venezuela",          "slug": "venezuela"},
]

TAG_CATEGORY_MAP = {
    "EventbriteCategory/103": EventCategory.Music,
    "EventbriteCategory/110": EventCategory.Food_Drink,
    "EventbriteCategory/108": EventCategory.Sports,
    "EventbriteCategory/105": EventCategory.Culture_Arts,
    "EventbriteCategory/113": EventCategory.Nightlife,
    "EventbriteCategory/104": EventCategory.Festival,
    "EventbriteCategory/111": EventCategory.Festival,
    "EventbriteCategory/107": EventCategory.Culture_Arts,
}

ISLAND_ENUM_MAP = {
    "Trinidad": Island.Trinidad,
    "Tobago": Island.Tobago,
    "Barbados": Island.Barbados,
    "Jamaica": Island.Jamaica,
    "St. Lucia": Island.St_Lucia,
    "Grenada": Island.Grenada,
    "Antigua": Island.Antigua,
    "Bahamas": Island.Bahamas,
    "Puerto Rico": Island.Puerto_Rico,
    "Dominican Republic": Island.Dominican_Republic,
    "Cayman Islands": Island.Cayman_Islands,
    "Curaçao": Island.Curacao,
}

EXPAND_FIELDS = ["event_sales_status", "image", "primary_venue", "ticket_availability", "primary_organizer"]
REQUEST_DELAY = 2.5
EVENTS_URL = "https://www.eventbrite.com/api/v3/destination/events/"

def _detect_island(venue: dict, default: str) -> Optional[Island]:
    address = venue.get("address") or {}
    text_parts = [
        address.get("city", ""), 
        address.get("region", ""),
        address.get("country", ""), 
        address.get("localized_area_display", ""),
        venue.get("name", "")
    ]
    full_text = " ".join([t for t in text_parts if t]).lower()
    
    mapping = {
        "trinidad": Island.trinidad, "tobago": Island.tobago, "barbados": Island.barbados,
        "jamaica": Island.jamaica, "saint lucia": Island.st_lucia, "grenada": Island.grenada,
        "antigua": Island.antigua, "bahamas": Island.bahamas, "puerto rico": Island.puerto_rico,
        "dominican republic": Island.dominican_republic, "cayman": Island.cayman, 
        "curacao": Island.curacao, "curaçao": Island.curacao
    }

    for kw, island_enum in mapping.items():
        if kw in full_text:
            return island_enum
            
    us_blacklist = [", GA", " GA ", "ATLANTA", ", TX", " TX ", "DALLAS", ", FL", " FL ", "MIAMI", "NY", "NEW YORK"]
    
    if any(state in full_text.upper() for state in us_blacklist):
        return None 

    return ISLAND_ENUM_MAP.get(default, Island.other)

def _normalize_price(ticket_info: dict) -> Optional[float]:
    if not ticket_info or ticket_info.get("is_free"):
        return None
    
    try:
        raw_val = (ticket_info.get("minimum_ticket_price") or {}).get("value")
        currency = (ticket_info.get("minimum_ticket_price") or {}).get("currency", "USD")
        if not raw_val:
            return None
            
        base_price = float(raw_val) / 100.0
        
        rates = {
            "TTD": 1.0, "USD": 6.8, "BBD": 3.4, "XCD": 2.5,
            "JMD": 0.043, "DOP": 0.11, "EUR": 7.3
        }
        
        return round(base_price * rates.get(currency.upper(), 6.8), 2)
    
    except:
        return None

def _map_category(tags: list) -> EventCategory:
    for tag in (tags or []):
        cat = TAG_CATEGORY_MAP.get(tag.get("tag", ""))
        
        if cat:
            return cat
        
    return EventCategory.other

def _parse_event(evt: dict, default_island_name: str) -> Optional[dict]:
    try:
        title = (evt.get("name") or "").strip()
        if not title:
            return None
        
        venue = evt.get("primary_venue") or {}
        island_enum = _detect_island(venue, default_island_name)
        
        if not island_enum:
            return None
        
        start_date = evt.get("start_date", "")
        start_time = evt.get("start_time", "00:00") or "00:00"
        date = datetime.fromisoformat(f"{start_date}T{start_time}")

        end_date_str = evt.get("end_date")
        end_date = None
        
        if end_date_str:
            try:
                end_date = datetime.fromisoformat(f"{end_date_str}T{evt.get('end_time', '00:00')}")
                
            except:
                pass

        return {
            "title": title,
            "description": (evt.get("summary") or "")[:2000],
            "island": island_enum,
            "venue": venue.get("name") or "TBA",
            "date": date,
            "end_date": end_date,
            "price": _normalize_price(evt.get("ticket_availability")),
            "category": _map_category(evt.get("tags")),
            "source_url": evt.get("url"),
            "image_url": (evt.get("image") or {}).get("url"),
        }
        
    except Exception as e:
        logger.debug(f"Error parsing Eventbrite event: {e}")
        
        return None

class EventbriteScraper:
    SOURCE_NAME = "Eventbrite"

    def __init__(self, cookie_header: str, csrf_token: str, referer: str):
        self.session = req.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": referer,
            "Cookie": cookie_header,
        })

    def _get_event_ids_from_html(self, slug: str) -> list[str]:
        url = f"https://www.eventbrite.com/d/{slug}/all-events/"
        time.sleep(REQUEST_DELAY)
        
        try:
            resp = self.session.get(url, timeout=15)
            if not resp.ok:
                return []
            
            ids = re.findall(r'/e/(?:.*?)-(\d{10,15})\?', resp.text)
            ids.extend(re.findall(r'"eid":"(\d{10,15})"', resp.text))
            
            return list(set(ids))
        
        except:
            return []

    def _fetch_events_by_ids(self, event_ids: list[str]) -> list[dict]:
        all_events = []
        
        for i in range(0, len(event_ids), 50):
            batch = event_ids[i:i + 50]
            time.sleep(REQUEST_DELAY)
            
            try:
                resp = self.session.get(EVENTS_URL, params={"event_ids": ",".join(batch), "expand": ",".join(EXPAND_FIELDS)}, timeout=15)
                if resp.ok:
                    all_events.extend(resp.json().get("events") or [])
                    
            except:
                continue
            
        return all_events

    def scrape(self) -> list[dict]:
        all_records, seen_urls = [], set()
        
        for loc in LOCATIONS:
            ids = self._get_event_ids_from_html(loc["slug"])
            if not ids:
                continue
            
            raw_events = self._fetch_events_by_ids(ids)
            
            for evt in raw_events:
                record = _parse_event(evt, loc["name"])
                
                if record and record["source_url"] not in seen_urls:
                    seen_urls.add(record["source_url"])
                    all_records.append(record)
                    
        return all_records

    def run(self, auto_publish: bool = False) -> dict:
        records = self.scrape()
        with get_cli_session() as session:
            return ScraperService(session).import_from_records(records, auto_publish=auto_publish)