"""
Skill: meteo in tempo reale via wttr.in (no API key).
Trigger: "che tempo fa", "meteo a Milano", "temperatura a Roma", "piove?", ecc.
"""
import re
from ._base import Skill

_WEATHER_RE = re.compile(
    r'\b(?:che\s+tempo\s+(?:fa|c\'è)|meteo|temperatura|previsioni?|'
    r'piove|nevica|fa\s+(?:caldo|freddo)|cielo)',
    re.I,
)
_CITY_RE = re.compile(
    r'\b(?:a|in|su|per)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s]{1,25}?)(?:\?|$|,|\s+(?:oggi|domani|adesso))',
    re.I,
)


class WeatherSkill(Skill):
    name        = "weather"
    description = "Meteo in tempo reale per qualsiasi città tramite wttr.in."

    def match(self, text: str) -> dict | None:
        if not _WEATHER_RE.search(text):
            return None
        city_m = _CITY_RE.search(text)
        city = city_m.group(1).strip() if city_m else "Milano"
        return {"city": city}

    async def run(self, user_input: str, params: dict) -> str:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self._fetch, params["city"]
        )

    def _fetch(self, city: str) -> str:
        try:
            import httpx
            r = httpx.get(
                f"https://wttr.in/{city}?format=j1&lang=it",
                timeout=8,
                headers={"User-Agent": "curl/7.88"},
            )
            r.raise_for_status()
            data = r.json()

            cc   = data["current_condition"][0]
            desc_list = cc.get("lang_it") or cc.get("weatherDesc") or [{}]
            desc = desc_list[0].get("value", "n/d")
            temp   = cc["temp_C"]
            feels  = cc["FeelsLikeC"]
            hum    = cc["humidity"]
            wind   = cc["windspeedKmph"]

            area_list = data.get("nearest_area", [{}])[0].get("areaName", [{}])
            area = area_list[0].get("value", city) if area_list else city

            # Previsione domani
            tomorrow = ""
            if len(data.get("weather", [])) > 1:
                w = data["weather"][1]
                t_max = w["maxtempC"]
                t_min = w["mintempC"]
                d_list = w.get("hourly", [{}])[4].get("lang_it") or \
                         w.get("hourly", [{}])[4].get("weatherDesc") or [{}]
                d = d_list[0].get("value", "") if d_list else ""
                tomorrow = f"\nDomani: {d}, {t_min}–{t_max}°C"

            return (
                f"[WEATHER: {area}]\n"
                f"{desc} · {temp}°C (percepita {feels}°C)\n"
                f"Umidità {hum}% · Vento {wind} km/h"
                f"{tomorrow}"
            )
        except Exception as e:
            return f"[WEATHER] Errore per {city}: {e}"
