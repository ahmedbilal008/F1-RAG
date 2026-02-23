"""OpenF1 live data client for real-time session augmentation."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime

import requests

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("openf1")


# Keywords that suggest the user wants live/current data
LIVE_DATA_KEYWORDS = [
    "current session", "live", "right now", "today's race",
    "qualifying results", "practice results", "current position",
    "latest lap", "weather at", "track temperature",
    "current standings today", "position right now",
]


def is_live_query(question: str) -> bool:
    """Detect if a question is about live/current session data."""
    q = question.lower()
    return any(kw in q for kw in LIVE_DATA_KEYWORDS)


class OpenF1Client:
    """Client for the OpenF1 API for live session data."""

    def __init__(self):
        settings = get_settings()
        self._base_url = settings.OPENF1_BASE_URL.rstrip("/")
        self._timeout = 10

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[List[Dict]]:
        """Make a GET request to OpenF1."""
        url = f"{self._base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params or {}, timeout=self._timeout)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else [data]
        except requests.RequestException as e:
            logger.warning(f"OpenF1 API error for {endpoint}: {e}")
            return None

    def get_latest_session(self) -> Optional[Dict[str, Any]]:
        """Get the latest/current F1 session."""
        data = self._get("sessions", {"session_key": "latest"})
        if data:
            session = data[0] if data else None
            if session:
                return {
                    "session_name": session.get("session_name", "Unknown"),
                    "session_type": session.get("session_type", "Unknown"),
                    "circuit": session.get("circuit_short_name", "Unknown"),
                    "country": session.get("country_name", "Unknown"),
                    "date_start": session.get("date_start", ""),
                    "date_end": session.get("date_end", ""),
                    "year": session.get("year", 0),
                }
        return None

    def get_current_positions(self) -> Optional[str]:
        """Get current driver positions in the latest session."""
        data = self._get("position", {"session_key": "latest"})
        if not data:
            return None

        # Get latest position for each driver
        driver_positions: Dict[int, Dict] = {}
        for entry in data:
            driver_num = entry.get("driver_number")
            if driver_num:
                driver_positions[driver_num] = entry

        if not driver_positions:
            return None

        # Sort by position
        sorted_drivers = sorted(
            driver_positions.values(),
            key=lambda x: x.get("position", 999),
        )

        lines = ["Current Session Positions:"]
        for d in sorted_drivers[:20]:
            pos = d.get("position", "?")
            num = d.get("driver_number", "?")
            lines.append(f"  P{pos}: Driver #{num}")

        return "\n".join(lines)

    def get_weather(self) -> Optional[str]:
        """Get current weather data for the session."""
        data = self._get("weather", {"session_key": "latest"})
        if not data:
            return None

        latest = data[-1] if data else None
        if not latest:
            return None

        return (
            f"Current Track Weather:\n"
            f"  Air Temperature: {latest.get('air_temperature', 'N/A')}°C\n"
            f"  Track Temperature: {latest.get('track_temperature', 'N/A')}°C\n"
            f"  Humidity: {latest.get('humidity', 'N/A')}%\n"
            f"  Rainfall: {'Yes' if latest.get('rainfall', 0) else 'No'}\n"
            f"  Wind Speed: {latest.get('wind_speed', 'N/A')} m/s"
        )

    def get_drivers_list(self) -> Optional[str]:
        """Get drivers in the latest session."""
        data = self._get("drivers", {"session_key": "latest"})
        if not data:
            return None

        lines = ["Drivers in Current Session:"]
        seen = set()
        for d in data:
            num = d.get("driver_number")
            if num and num not in seen:
                seen.add(num)
                name = d.get("full_name", f"Driver #{num}")
                team = d.get("team_name", "Unknown")
                lines.append(f"  #{num} {name} - {team}")

        return "\n".join(lines) if len(lines) > 1 else None

    def get_live_context(self) -> str:
        """Aggregate all available live data into context string."""
        parts = []

        session = self.get_latest_session()
        if session:
            parts.append(
                f"Latest F1 Session: {session['session_name']} "
                f"({session['session_type']}) at {session['circuit']}, "
                f"{session['country']} ({session['year']})"
            )

        drivers = self.get_drivers_list()
        if drivers:
            parts.append(drivers)

        positions = self.get_current_positions()
        if positions:
            parts.append(positions)

        weather = self.get_weather()
        if weather:
            parts.append(weather)

        if parts:
            return "\n\n".join(parts)
        return "No live F1 session data is currently available."


_client: Optional[OpenF1Client] = None


def get_openf1_client() -> OpenF1Client:
    """Get or create the singleton OpenF1 client."""
    global _client
    if _client is None:
        _client = OpenF1Client()
    return _client
