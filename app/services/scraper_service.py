# PATH: app/services/scraper_service.py
import csv
import logging
from datetime import datetime
from typing import Optional
from sqlmodel import Session
from app.repositories.event import EventRepository
from app.schemas.event import EventCreate
from app.models.event import Island, EventCategory, EventStatus

logger = logging.getLogger(__name__)

DATE_FORMATS = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d"]

def _parse_date(raw: str) -> Optional[datetime]:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt)
        
        except ValueError:
            continue
        
    logger.warning(f"Could not parse date: {raw}")
    
    return None

def _map_island(raw: str) -> Island:
    raw = raw.strip().lower()
    for member in Island:
        if raw in member.value.lower() or member.name.lower() == raw:
            return member
        
    return Island.other

def _map_category(raw: str) -> EventCategory:
    raw = raw.strip().lower()
    for member in EventCategory:
        if raw in member.value.lower() or member.name.lower() == raw:
            return member
        
    return EventCategory.other

class ScraperService:

    def __init__(self, session: Session):
        self.repo = EventRepository(session)

    def import_from_csv(self, filepath: str, auto_publish: bool = False) -> dict:
        created = 0
        skipped = 0
        errors = []

        with open(filepath, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            reader.fieldnames = [h.strip().lower() for h in (reader.fieldnames or [])]

            for i, row in enumerate(reader, start=2):
                try:
                    date = _parse_date(row.get("date", ""))
                    if not date:
                        errors.append(f"Row {i}: invalid date '{row.get('date')}'")
                        continue

                    price_raw = row.get("price", "").strip()
                    price = float(price_raw.replace("$", "").replace(",", "")) if price_raw else None

                    status = EventStatus.published if auto_publish else EventStatus.pending

                    data = EventCreate(
                        title=row["title"].strip(),
                        description=row.get("description", "").strip(),
                        island=_map_island(row.get("island", "")),
                        venue=row.get("venue", "").strip(),
                        date=date,
                        end_date=_parse_date(row["end_date"]) if row.get("end_date") else None,
                        price=price,
                        category=_map_category(row.get("category", "")),
                        source_url=row.get("source_url", "").strip() or None,
                        image_url=row.get("image_url", "").strip() or None,
                        status=status,
                    )
                    event = self.repo.upsert_from_scrape(data)
                    if event.id and event.title == data.title:
                        created += 1
                        
                    else:
                        skipped += 1

                except KeyError as e:
                    errors.append(f"Row {i}: missing column {e}")
                    
                except Exception as e:
                    errors.append(f"Row {i}: {e}")

        logger.info(f"CSV import complete — created: {created}, skipped: {skipped}, errors: {len(errors)}")
        return {"created": created, "skipped": skipped, "errors": errors}

    def import_from_records(self, records: list[dict], auto_publish: bool = False) -> dict:
        created = 0
        skipped = 0
        errors = []

        for i, row in enumerate(records):
            try:
                status = EventStatus.published if auto_publish else EventStatus.pending
                data = EventCreate(status=status, **row)
                self.repo.upsert_from_scrape(data)
                created += 1
                
            except Exception as e:
                errors.append(f"Record {i}: {e}")

        return {"created": created, "skipped": skipped, "errors": errors}
