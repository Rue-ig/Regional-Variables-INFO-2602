"""
trinijunglejuice.com scraper.
"""
import logging, requests
from datetime import datetime, timezone
from typing import Optional
from app.database import get_cli_session
from app.services.scraper_service import ScraperService

logger = logging.getLogger(__name__)

API_URL = "https://staging.trinijunglejuice.com/api/events"

CATEGORY_MAP = {
    "Carnival": "Carnival",
    "Soca / Calypso": "Music",
    "Reggae / Dancehall": "Music",
    "DJ Party": "Nightlife",
    "All Inclusive (Food & Drink)": "Food & Drink",
    "Sports": "Sports",
    "Culture": "Culture & Arts",
}

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

def _map_category(categories: list) -> str:
    for cat in categories:
        title = cat.get("title", "")
        if title in CATEGORY_MAP:
            return CATEGORY_MAP[title]
    return "Other"

class TJJScraper:
    SOURCE_NAME = "trinijunglejuice.com"

    def scrape(self) -> list[dict]:
        try:
            resp = requests.get(
                API_URL,
                params={"page": 1, "items": 10000, "type": "featured"},
                headers={"User-Agent": "CaribbeanEventsBot/1.0"},
                timeout=15,
            )
            resp.raise_for_status()
            events = resp.json().get("data", [])
        except Exception as e:
            logger.error(f"TJJ API error: {e}")
            return []

        records = []
        for ev in events:
            try:
                title = (ev.get("title") or "").strip()
                if not title:
                    continue

                start_raw = ev.get("start_datetime")
                if not start_raw:
                    continue
                date = datetime.fromisoformat(start_raw.replace("Z", "+00:00")).replace(tzinfo=None)

                end_raw = ev.get("end_datetime")
                end_date = None
                if end_raw:
                    try:
                        end_date = datetime.fromisoformat(end_raw.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception:
                        pass

                location = ev.get("location") or {}
                island   = _detect_island(location)

                if island == "Other":
                    non_caribbean = ["united states", "canada", "united kingdom"]
                    country = (location.get("country") or "").lower()
                    if any(nc in country for nc in non_caribbean):
                        continue

                price_raw = ev.get("cost_per_person")
                price: Optional[float] = None
                if price_raw:
                    try:
                        price = float(price_raw) or None
                    except (ValueError, TypeError):
                        pass

                records.append({
                    "title":       title,
                    "description": (ev.get("description") or "")[:2000],
                    "island":      island,
                    "venue":       location.get("address") or location.get("city") or "TBA",
                    "date":        date,
                    "end_date":    end_date,
                    "price":       price,
                    "category":   _map_category(ev.get("event_categories") or []),
                    "source_url":  ev.get("registration_url") or f"https://trinijunglejuice.com/events/{ev.get('slug','')}",
                    "image_url":   ev.get("poster_url"),
                })
            except Exception as e:
                logger.debug(f"TJJ: skipping event: {e}")

        logger.info(f"TJJ: {len(records)} events scraped")
        return records

    def run(self, auto_publish: bool = False) -> dict:
        records = self.scrape()
        with get_cli_session() as session:
            return ScraperService(session).import_from_records(records, auto_publish=auto_publish)
