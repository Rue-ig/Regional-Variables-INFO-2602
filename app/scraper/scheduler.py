# PATH: app/scraper/scheduler.py
"""
Runs all registered scrapers on a schedule.

Usage:
    python -m app.scraper.scheduler             # run once
    python -m app.scraper.scheduler --loop      # repeat every N hours
    python -m app.scraper.scheduler --loop --interval 6
    python -m app.scraper.scheduler --publish   # auto-publish results
    python -m app.scraper.scheduler --only ticketmaster   # run one scraper by name
"""

import sys, os, logging, argparse, time
from datetime import datetime
from app.config import get_settings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger("scheduler")

def _build_scrapers(settings, only: str = ""):
    scrapers = []

    if not only or only == "ticketmaster":
        if settings.ticketmaster_api_key:
            from app.scraper.site_scrapers.ticketmaster_scraper import TicketmasterScraper
            scrapers.append(("Ticketmaster", TicketmasterScraper(settings.ticketmaster_api_key)))
        else:
            logger.warning(
                "TICKETMASTER_API_KEY not set — skipping Ticketmaster.\n"
                "  Register free at https://developer.ticketmaster.com"
            )

    if not only or only == "eventbrite":
        if settings.eventbrite_cookie_header and settings.eventbrite_csrf_token:
            from app.scraper.site_scrapers.eventbrite_scraper import EventbriteScraper
            scrapers.append(("Eventbrite", EventbriteScraper(
                cookie_header=settings.eventbrite_cookie_header,
                csrf_token=settings.eventbrite_csrf_token,
                referer=settings.eventbrite_referer,
            )))
            
        else:
            logger.warning(
                "EVENTBRITE_COOKIE_HEADER or EVENTBRITE_CSRF_TOKEN not set — skipping Eventbrite.\n"
                "  See eventbrite_scraper.py docstring for how to get these (5 min)."
            )

    if not only or only == "islandetickets":
        from app.scraper.site_scrapers.islandetickets_scraper import IslandeTicketsScraper
        scrapers.append(("islandetickets.com", IslandeTicketsScraper()))

    if not only or only == "tjj":
        from app.scraper.site_scrapers.trinijunglejuice_scraper import TJJScraper
        scrapers.append(("trinijunglejuice.com", TJJScraper()))

    if not only or only == "caribbeanevents":
        from app.scraper.site_scrapers.caribbeanevents_scraper import CaribbeanEventsScraper
        scrapers.append(("caribbeanevents.com", CaribbeanEventsScraper()))

    return scrapers

def run_all(auto_publish: bool = False, only: str = "") -> None:
    settings = get_settings()

    scrapers = _build_scrapers(settings, only=only)
    
    if not scrapers:
        logger.warning("No scrapers are active. Check your .env configuration.")
        
        return

    logger.info(f"Starting scrape run — {len(scrapers)} scraper(s)")
    start  = datetime.utcnow()
    totals = {"created": 0, "skipped": 0, "errors": 0}

    for name, scraper in scrapers:
        try:
            logger.info(f"Running {name}…")
            result = scraper.run(auto_publish=auto_publish)
            totals["created"] += result.get("created", 0)
            totals["skipped"] += result.get("skipped", 0)
            totals["errors"]  += len(result.get("errors", []))
            logger.info(
                f"{name}: created={result.get('created',0)} "
                f"skipped={result.get('skipped',0)} "
                f"errors={len(result.get('errors',[]))}"
            )
            
            if result.get("errors"):
                for err in result["errors"][:5]:
                    logger.warning(f"  {name} error: {err}")
                    
        except Exception as e:
            logger.error(f"{name} failed: {e}", exc_info=True)
            totals["errors"] += 1

    elapsed = (datetime.utcnow() - start).total_seconds()
    logger.info(
        f"Run complete in {elapsed:.1f}s — "
        f"created: {totals['created']}, "
        f"skipped: {totals['skipped']}, "
        f"errors: {totals['errors']}"
    )


def main():
    parser = argparse.ArgumentParser(description="Caribbean Events scraper scheduler")
    parser.add_argument("--loop",     action="store_true", help="Run on a repeating schedule")
    parser.add_argument("--interval", type=int, default=12, help="Hours between runs (default: 12)")
    parser.add_argument("--publish",  action="store_true", help="Auto-publish imported events")
    parser.add_argument(
        "--only",
        default="",
        help="Run only one scraper by short name: ticketmaster, eventbrite, islandetickets, tjj, caribbeanevents, compass",
    )
    args = parser.parse_args()

    if args.loop:
        logger.info(f"Scheduler started — running every {args.interval}h")
        
        while True:
            run_all(auto_publish=args.publish, only=args.only)
            logger.info(f"Next run in {args.interval}h")
            time.sleep(args.interval * 3600)
            
    else:
        run_all(auto_publish=args.publish, only=args.only)

if __name__ == "__main__":
    main()
