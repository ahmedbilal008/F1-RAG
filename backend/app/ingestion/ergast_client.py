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

BASE = "https://api.jolpi.ca/ergast/f1"

JOLPICA_ENDPOINTS: Dict[str, Any] = {
    "result_years":       [2024, 2025],
    "standing_years":     [2024, 2025],

    "driver_years":       [2024, 2025, 2026],
    "constructor_years":  [2024, 2025, 2026],

    "circuits": f"{BASE}/circuits.json",

    "season_races":          "{base}/{year}/races.json",
    "race_results":          "{base}/{year}/{round}/results.json",
    "driver_standings":      "{base}/{year}/driverStandings.json",
    "constructor_standings": "{base}/{year}/constructorStandings.json",
    "season_drivers":        "{base}/{year}/drivers.json",
    "season_constructors":   "{base}/{year}/constructors.json",
}


class ErgastClient:
    """Client for Jolpica F1 API (Ergast replacement)."""

    def __init__(self):
        settings = get_settings()
        self._base = BASE
        self._timeout = settings.SCRAPE_TIMEOUT
        self._delay = settings.SCRAPE_DELAY

    def _get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            resp = requests.get(url, params=params, timeout=self._timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"API error {url}: {e}")
            return None

    def _url(self, template_key: str, **kwargs) -> str:
        return JOLPICA_ENDPOINTS[template_key].format(base=self._base, **kwargs)

    def _get_race_schedule(self, year: int) -> List[Dict]:
        url = self._url("season_races", year=year)
        data = self._get(url)
        if not data:
            return []
        return data.get("MRData", {}).get("RaceTable", {}).get("Races", [])

    def _fetch_race_result(self, year: int, round_num: int, race_name: str) -> Optional[ScrapedDocument]:
        url = self._url("race_results", year=year, round=round_num)
        data = self._get(url)
        if not data:
            return None

        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            return None

        race = races[0]
        circuit = race.get("Circuit", {}).get("circuitName", "")
        country = race.get("Circuit", {}).get("Location", {}).get("country", "")
        date = race.get("date", "")
        results = race.get("Results", [])

        lines = [
            f"{year} {race_name}",
            f"Circuit: {circuit}, {country}",
            f"Date: {date}",
            "Race Result:",
        ]
        for r in results:
            pos = r.get("position", "?")
            driver = f"{r.get('Driver', {}).get('givenName', '')} {r.get('Driver', {}).get('familyName', '')}".strip()
            constructor = r.get("Constructor", {}).get("name", "")
            grid = r.get("grid", "?")
            laps = r.get("laps", "?")
            status = r.get("status", "")
            points = r.get("points", "0")
            fastest_lap = r.get("FastestLap", {}).get("Time", {}).get("time", "")
            time_str = r.get("Time", {}).get("time", status)
            line = f"  P{pos}: {driver} ({constructor}) | Grid: {grid} | Laps: {laps} | Time: {time_str} | Points: {points}"
            if fastest_lap:
                line += f" | Fastest Lap: {fastest_lap}"
            lines.append(line)

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} {race_name} Result",
            url=url,
            category="race_results",
            priority=1,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )
    
    def _fetch_driver_standings(self, year: int) -> Optional[ScrapedDocument]:
        url = self._url("driver_standings", year=year)
        data = self._get(url)
        if not data:
            return None

        lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        if not lists:
            return None

        driver_standings = lists[0].get("DriverStandings", [])
        round_num = lists[0].get("round", "final")

        lines = [f"Formula 1 {year} Drivers Championship Standings (after round {round_num})"]
        for s in driver_standings:
            pos = s.get("position", "?")
            points = s.get("points", "0")
            wins = s.get("wins", "0")
            d = s.get("Driver", {})
            name = f"{d.get('givenName', '')} {d.get('familyName', '')}".strip()
            nationality = d.get("nationality", "")
            constructor = s.get("Constructors", [{}])[0].get("name", "") if s.get("Constructors") else ""
            lines.append(f"  P{pos}: {name} ({nationality}) | Team: {constructor} | Points: {points} | Wins: {wins}")

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} Drivers Championship Standings",
            url=url,
            category="standings",
            priority=1,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )

    def _fetch_constructor_standings(self, year: int) -> Optional[ScrapedDocument]:
        url = self._url("constructor_standings", year=year)
        data = self._get(url)
        if not data:
            return None

        lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        if not lists:
            return None

        const_standings = lists[0].get("ConstructorStandings", [])
        round_num = lists[0].get("round", "final")

        lines = [f"Formula 1 {year} Constructors Championship Standings (after round {round_num})"]
        for s in const_standings:
            pos = s.get("position", "?")
            points = s.get("points", "0")
            wins = s.get("wins", "0")
            c = s.get("Constructor", {})
            name = c.get("name", "")
            nationality = c.get("nationality", "")
            lines.append(f"  P{pos}: {name} ({nationality}) | Points: {points} | Wins: {wins}")

        content = "\n".join(lines)
        return ScrapedDocument(
            content=content,
            title=f"{year} Constructors Championship Standings",
            url=url,
            category="standings",
            priority=1,
            scraped_at=datetime.utcnow().isoformat(),
            content_length=len(content),
        )

    def _fetch_drivers(self, year: int) -> List[ScrapedDocument]:
        url = self._url("season_drivers", year=year)
        data = self._get(url)
        if not data:
            return []

        drivers = data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])
        docs = []
        for d in drivers:
            name = f"{d.get('givenName', '')} {d.get('familyName', '')}".strip()
            content = (
                f"Driver: {name}\n"
                f"Season: {year}\n"
                f"Code: {d.get('code', 'N/A')}\n"
                f"Permanent number: #{d.get('permanentNumber', 'N/A')}\n"
                f"Nationality: {d.get('nationality', '')}\n"
                f"Date of birth: {d.get('dateOfBirth', '')}\n"
                f"Wikipedia: {d.get('url', '')}"
            )
            docs.append(ScrapedDocument(
                content=content,
                title=f"{name} â€” {year} F1 Driver",
                url=url,
                category="drivers",
                priority=1,
                scraped_at=datetime.utcnow().isoformat(),
                content_length=len(content),
            ))
        return docs

    def _fetch_constructors(self, year: int) -> List[ScrapedDocument]:
        url = self._url("season_constructors", year=year)
        data = self._get(url)
        if not data:
            return []

        constructors = data.get("MRData", {}).get("ConstructorTable", {}).get("Constructors", [])
        docs = []
        for c in constructors:
            content = (
                f"Constructor: {c.get('name', '')}\n"
                f"Season: {year}\n"
                f"Nationality: {c.get('nationality', '')}\n"
                f"Wikipedia: {c.get('url', '')}"
            )
            docs.append(ScrapedDocument(
                content=content,
                title=f"{c.get('name', '')} â€” {year} F1 Constructor",
                url=url,
                category="constructors",
                priority=1,
                scraped_at=datetime.utcnow().isoformat(),
                content_length=len(content),
            ))
        return docs

    def _fetch_circuits(self) -> List[ScrapedDocument]:
        data = self._get(JOLPICA_ENDPOINTS["circuits"], params={"limit": 200})
        if not data:
            return []

        circuits = data.get("MRData", {}).get("CircuitTable", {}).get("Circuits", [])
        docs = []
        for c in circuits:
            loc = c.get("Location", {})
            content = (
                f"Circuit: {c.get('circuitName', '')}\n"
                f"Circuit ID: {c.get('circuitId', '')}\n"
                f"City: {loc.get('locality', '')}\n"
                f"Country: {loc.get('country', '')}\n"
                f"Latitude: {loc.get('lat', '')}\n"
                f"Longitude: {loc.get('long', '')}\n"
                f"Wikipedia: {c.get('url', '')}"
            )
            docs.append(ScrapedDocument(
                content=content,
                title=f"{c.get('circuitName', '')} â€” F1 Circuit",
                url=JOLPICA_ENDPOINTS["circuits"],
                category="circuits",
                priority=2,
                scraped_at=datetime.utcnow().isoformat(),
                content_length=len(content),
            ))
        return docs

    def fetch_all(
        self,
        years: Optional[List[int]] = None,
    ) -> tuple[List[ScrapedDocument], Dict[str, Any]]:
        documents: List[ScrapedDocument] = []
        stats: Dict[str, Any] = {"total": 0, "success": 0, "failed": 0, "errors": []}

        def _add(doc_or_list, label: str):
            stats["total"] += 1
            if isinstance(doc_or_list, list):
                if doc_or_list:
                    documents.extend(doc_or_list)
                    stats["success"] += 1
                    logger.info(f"  {label}: {len(doc_or_list)} docs")
                else:
                    stats["failed"] += 1
                    stats["errors"].append(f"Empty: {label}")
            else:
                if doc_or_list:
                    documents.append(doc_or_list)
                    stats["success"] += 1
                    logger.info(f"  {label}: 1 doc")
                else:
                    stats["failed"] += 1
                    stats["errors"].append(f"Empty: {label}")

        # Circuits (all-time, one fetch)
        logger.info("Fetching circuits...")
        _add(self._fetch_circuits(), "circuits")
        time.sleep(self._delay)

        # Race results, qualifying, sprint â€” per round
        for year in JOLPICA_ENDPOINTS["result_years"]:
            logger.info(f"Fetching {year} race schedule...")
            schedule = self._get_race_schedule(year)
            if not schedule:
                logger.warning(f"No schedule for {year}")
                continue

            for race in schedule:
                rnd = race.get("round", "")
                name = race.get("raceName", f"Round {rnd}")
                _add(self._fetch_race_result(year, rnd, name), f"{year} R{rnd} {name}")
                time.sleep(self._delay)

        # Standings
        for year in JOLPICA_ENDPOINTS["standing_years"]:
            logger.info(f"Fetching {year} standings...")
            _add(self._fetch_driver_standings(year), f"{year} driver standings")
            time.sleep(self._delay)
            _add(self._fetch_constructor_standings(year), f"{year} constructor standings")
            time.sleep(self._delay)

        # Driver roster (includes 2026 confirmed grid)
        for year in JOLPICA_ENDPOINTS["driver_years"]:
            logger.info(f"Fetching {year} drivers...")
            _add(self._fetch_drivers(year), f"{year} drivers")
            time.sleep(self._delay)

        # Constructor roster (includes 2026)
        for year in JOLPICA_ENDPOINTS["constructor_years"]:
            logger.info(f"Fetching {year} constructors...")
            _add(self._fetch_constructors(year), f"{year} constructors")
            time.sleep(self._delay)

        logger.info(
            f"Ergast fetch complete: {stats['success']} ok, "
            f"{stats['failed']} failed out of {stats['total']} calls | "
            f"{len(documents)} documents total"
        )
        return documents, stats
