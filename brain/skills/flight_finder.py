"""
Skill: cerca voli e restituisce link diretti a Google Flights / Skyscanner.
Trigger: "cerca voli", "volo da X a Y", "voli per X", "aereo per X", ecc.
"""
import re
import logging
from ._base import Skill

log = logging.getLogger("skill.flight_finder")

_FLIGHT_RE = re.compile(
    r'\b(?:cerca\s+voli?|voli?\s+(?:da|per|verso|a)\b|'
    r'volo\s+(?:da|per|verso|a)\b|'
    r'aereo\s+(?:da|per|verso|a)\b|'
    r'quanto\s+costa\s+(?:volare|andare\s+in\s+aereo)\b|'
    r'prezzo\s+volo|biglietto\s+aereo|'
    r'volare\s+(?:da|per|verso|a)\b)',
    re.I,
)

_FROM_RE = re.compile(
    r'\b(?:da|dall[ao]?)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s]{1,20}?)\s+(?:per|a|verso)\s',
    re.I,
)

_TO_RE = re.compile(
    r'\b(?:per|a|verso)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s]{1,20}?)'
    r'(?:\s+il\s+\d|\s+(?:domani|dopodomani|lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica)|\s*[,?]|\s*$)',
    re.I,
)

_DATE_RE = re.compile(
    r'\b(?:il\s+)?(\d{1,2}[/\-\.]\d{1,2}(?:[/\-\.]\d{2,4})?|'
    r'domani|dopodomani|'
    r'(?:lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica)(?:\s+prossim[oa])?)',
    re.I,
)

_IATA = {
    "roma": "FCO", "milano": "MXP", "milan": "MXP", "venezia": "VCE",
    "napoli": "NAP", "catania": "CTA", "palermo": "PMO", "bari": "BRI",
    "bologna": "BLQ", "firenze": "FLR", "torino": "TRN", "cagliari": "CAG",
    "bergamo": "BGY", "pisa": "PSA", "verona": "VRN", "genova": "GOA",
    "brindisi": "BDS", "lamezia terme": "SUF", "reggio calabria": "REG",
    "londra": "LHR", "parigi": "CDG", "barcellona": "BCN", "madrid": "MAD",
    "amsterdam": "AMS", "berlino": "BER", "dublino": "DUB", "vienna": "VIE",
    "lisbona": "LIS", "praga": "PRG", "budapest": "BUD", "varsavia": "WAW",
    "stoccolma": "ARN", "oslo": "OSL", "copenaghen": "CPH", "copenhagen": "CPH",
    "atene": "ATH", "istanbul": "IST", "zurigo": "ZRH", "bruxelles": "BRU",
    "new york": "JFK", "los angeles": "LAX", "tokyo": "NRT", "dubai": "DXB",
    "toronto": "YYZ", "sydney": "SYD", "miami": "MIA", "chicago": "ORD",
}


def _iata(city: str) -> str:
    return _IATA.get(city.strip().lower(), city.upper()[:3])


def _date_to_iso(raw: str) -> str:
    from datetime import date, timedelta
    today = date.today()
    d = raw.strip().lower()
    if d == "domani":
        return (today + timedelta(days=1)).isoformat()
    if d == "dopodomani":
        return (today + timedelta(days=2)).isoformat()
    weekdays = {"lunedì": 0, "martedì": 1, "mercoledì": 2, "giovedì": 3,
                "venerdì": 4, "sabato": 5, "domenica": 6}
    for name, wd in weekdays.items():
        if name in d:
            delta = (wd - today.weekday()) % 7 or 7
            return (today + timedelta(days=delta)).isoformat()
    m = re.match(r'(\d{1,2})[/\-\.](\d{1,2})(?:[/\-\.](\d{2,4}))?', d)
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if year < 100:
            year += 2000
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            pass
    return ""


class FlightFinderSkill(Skill):
    name        = "flight_finder"
    description = "Cerca voli e costruisce link a Google Flights / Skyscanner."

    def match(self, text: str) -> dict | None:
        if not _FLIGHT_RE.search(text):
            return None
        from_m = _FROM_RE.search(text)
        to_m   = _TO_RE.search(text)
        date_m = _DATE_RE.search(text)
        return {
            "origin":      from_m.group(1).strip() if from_m else "",
            "destination": to_m.group(1).strip()   if to_m   else "",
            "date_raw":    date_m.group(1).strip()  if date_m else "",
        }

    async def run(self, user_input: str, params: dict) -> str:
        origin = params.get("origin", "")
        dest   = params.get("destination", "")
        date_raw = params.get("date_raw", "")

        date_iso = _date_to_iso(date_raw) if date_raw else ""

        if not dest:
            return (
                "[FLIGHT FINDER] Non ho capito la destinazione.\n"
                "Esempio: 'cerca voli da Milano a Roma domani'"
            )

        orig_iata = _iata(origin) if origin else "IT"
        dest_iata = _iata(dest)

        # Google Flights URL
        query = f"Voli {origin + ' ' if origin else ''}{dest}"
        gf_url = f"https://www.google.com/travel/flights?q={query.replace(' ', '+')}&hl=it&curr=EUR"

        # Skyscanner URL
        sky_base = f"https://www.skyscanner.it/trasporti/voli/{orig_iata.lower()}/{dest_iata.lower()}/"
        if date_iso:
            sky_url = sky_base + date_iso.replace("-", "") + "/"
        else:
            sky_url = sky_base

        lines = ["[FLIGHT FINDER]"]
        if origin:
            lines.append(f"Tratta: {origin.title()} ({orig_iata}) → {dest.title()} ({dest_iata})")
        else:
            lines.append(f"Destinazione: {dest.title()} ({dest_iata})")
        if date_iso:
            lines.append(f"Data: {date_iso}")

        lines.append(f"\nGoogle Flights: {gf_url}")
        lines.append(f"Skyscanner: {sky_url}")
        lines.append('\nDì "apri Google Flights" o "apri Skyscanner" per aprire nel browser.')

        return "\n".join(lines)
