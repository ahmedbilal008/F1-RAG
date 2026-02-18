"""Jolpica F1 API client for structured historical data (Ergast replacement)."""

from __future__ import annotations

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

import requests

from app.core.config import get_settings
from app.core.logging import get_logger
from app.ingestion.wikipedia_scraper import ScrapedDocument

logger = get_logger("ergast_client")


class ErgastClient:
    """Client for Jolpica F1 API (Ergast replacement)."""

    def __init__(self):
        settings = get_settings()
        self._base_url = settings.ERGAST_BASE_URL.rstrip("/")
        self._timeout = settings.SCRAPE_TIMEOUT
        self._delay = settings.SCRAPE_DELAY

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{self._base_url}/{endpoint}.json"
        try:
            response = requests.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ergast API error for {endpoint}: {e}")
            return None

    def _fetch_season_results(self, year: int) -> Optional[ScrapedDocument]:
        data = self._get(f"{year}/results", {"limit": 500})
        if not data:
            return None

        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            return None

        lines = [f"Formula 1 {year} Season Race Results\n"]
        for race in races:
            race_name = race.get("raceName", "Unknown GP")
            circuit = race.get("Circuit", {}).get("circuitName", "")
            date = race.get("date", "")
            results = race.get("Results", [])

            lines.append(f"\n{race_name} - {circuit} ({date})")
            for r in results[:10]:  # Top 10
                pos = r.get("position", "?")
                driver = f"{r.get('Driver', {}).get('givenName', '')} {r.get('Driver', {}).get('familyName', '')}".strip()
                constructor = r.get("Constructor", {}).get("name", "")
                status = r.get("status", "")
                time_str = r.get("Time", {}).get("time", status)
                lines.append(f"  P{pos}: {driver} ({constructor}) - {time_str}")

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} Season Race Results",
            url=f"{self._base_url}/{year}/results",
            category="race_results",
            priority=1,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )

    def _fetch_driver_standings(self, year: int) -> Optional[ScrapedDocument]:
        """Fetch driver championship standings."""
        data = self._get(f"{year}/driverStandings")
        if not data:
            return None

        standings = (
            data.get("MRData", {})
            .get("StandingsTable", {})
            .get("StandingsLists", [])
        )
        if not standings:
            return None

        driver_standings = standings[0].get("DriverStandings", [])

        lines = [f"Formula 1 {year} Drivers' Championship Standings\n"]
        for s in driver_standings:
            pos = s.get("position", "?")
            points = s.get("points", "0")
            wins = s.get("wins", "0")
            driver = s.get("Driver", {})
            name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip()
            nationality = driver.get("nationality", "")
            constructor = s.get("Constructors", [{}])[0].get("name", "") if s.get("Constructors") else ""
            lines.append(f"P{pos}: {name} ({nationality}) - {constructor} - {points} points, {wins} wins")

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} Drivers Championship",
            url=f"{self._base_url}/{year}/driverStandings",
            category="standings",
            priority=1,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )

    def _fetch_constructor_standings(self, year: int) -> Optional[ScrapedDocument]:
        """Fetch constructor championship standings."""
        data = self._get(f"{year}/constructorStandings")
        if not data:
            return None

        standings = (
            data.get("MRData", {})
            .get("StandingsTable", {})
            .get("StandingsLists", [])
        )
        if not standings:
            return None

        const_standings = standings[0].get("ConstructorStandings", [])

        lines = [f"Formula 1 {year} Constructors' Championship Standings\n"]
        for s in const_standings:
            pos = s.get("position", "?")
            points = s.get("points", "0")
            wins = s.get("wins", "0")
            constructor = s.get("Constructor", {})
            name = constructor.get("name", "")
            nationality = constructor.get("nationality", "")
            lines.append(f"P{pos}: {name} ({nationality}) - {points} points, {wins} wins")

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} Constructors Championship",
            url=f"{self._base_url}/{year}/constructorStandings",
            category="standings",
            priority=1,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )

    def _fetch_drivers_info(self, year: int) -> Optional[ScrapedDocument]:
        """Fetch driver information for a season."""
        data = self._get(f"{year}/drivers")
        if not data:
            return None

        drivers = data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])
        if not drivers:
            return None

        lines = [f"Formula 1 {year} Season Drivers\n"]
        for d in drivers:
            name = f"{d.get('givenName', '')} {d.get('familyName', '')}".strip()
            nationality = d.get("nationality", "")
            dob = d.get("dateOfBirth", "")
            number = d.get("permanentNumber", "N/A")
            code = d.get("code", "")
            lines.append(f"{name} ({code}) - #{number} - {nationality} - Born: {dob}")

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} Drivers Info",
            url=f"{self._base_url}/{year}/drivers",
            category="drivers",
            priority=2,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )

    def _fetch_constructors_info(self, year: int) -> Optional[ScrapedDocument]:
        """Fetch constructor info for a season."""
        data = self._get(f"{year}/constructors")
        if not data:
            return None

        constructors = data.get("MRData", {}).get("ConstructorTable", {}).get("Constructors", [])
        if not constructors:
            return None

        lines = [f"Formula 1 {year} Season Constructors/Teams\n"]
        for c in constructors:
            name = c.get("name", "")
            nationality = c.get("nationality", "")
            lines.append(f"{name} ({nationality})")

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} Constructors Info",
            url=f"{self._base_url}/{year}/constructors",
            category="constructors",
            priority=2,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )

    def fetch_all(
        self,
        years: Optional[List[int]] = None,
    ) -> tuple[List[ScrapedDocument], Dict[str, Any]]:
        """Fetch all configured data from the API."""
        target_years = years or [2020, 2021, 2022, 2023, 2024, 2025]
        documents: List[ScrapedDocument] = []
        stats = {"total": 0, "success": 0, "failed": 0, "errors": []}

        fetchers = [
            ("results", self._fetch_season_results),
            ("driver_standings", self._fetch_driver_standings),
            ("constructor_standings", self._fetch_constructor_standings),
            ("drivers", self._fetch_drivers_info),
            ("constructors", self._fetch_constructors_info),
        ]

        for year in target_years:
            for name, fetcher in fetchers:
                stats["total"] += 1
                try:
                    doc = fetcher(year)
                    if doc:
                        documents.append(doc)
                        stats["success"] += 1
                        logger.info(f"Fetched {name} for {year}")
                    else:
                        stats["failed"] += 1
                        stats["errors"].append(f"No data: {name} {year}")
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"Error: {name} {year}: {e}")
                    logger.error(f"Error fetching {name} for {year}: {e}")

                time.sleep(self._delay)

        logger.info(
            f"Ergast fetch complete: {stats['success']} ok, "
            f"{stats['failed']} failed out of {stats['total']}"
        )
        return documents, stats
