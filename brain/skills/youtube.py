"""
Skill: cerca video YouTube e estrae metadati/trascrizioni senza scaricare.
Trigger:
  - URL youtube.com / youtu.be nel testo
  - "cerca su youtube X", "trova video di X su youtube"
  - "trascrivi/cosa dice questo video: [URL]"
"""
import asyncio
import logging
import re
from ._base import Skill

log = logging.getLogger("skill.youtube")

_YT_URL_RE = re.compile(
    r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([\w\-]+)',
    re.I,
)

_SEARCH_RE = re.compile(
    # "cerca su youtube QUERY" / "cerca youtube QUERY"
    r'\b(?:cerca|trova|ricerca|mostrami|cercami)\s+(?:\w+\s+){0,3}(?:su\s+)?(?:youtube|yt)\s+(.+)'
    # "cerca/trova QUERY su youtube"
    r'|\b(?:cerca|trova|ricerca|mostrami|cercami)\s+(.+?)\s+su\s+(?:youtube|yt)\b'
    # "youtube: QUERY"
    r'|(?:youtube|yt)[,:]?\s+(?:cerca|trova|video|clip)?\s+(.+)',
    re.I,
)

_TRANSCRIPT_RE = re.compile(
    r'\b(?:trascrivi|cosa\s+dice|leggi|sottotitoli|trascrizione)\b',
    re.I,
)

_MAX_DESC   = 500
_MAX_SUB    = 4000


class YoutubeSkill(Skill):
    name        = "youtube"
    description = "Cerca video YouTube e recupera metadati, durata, trascrizioni."

    def match(self, text: str) -> dict | None:
        # URL YouTube esplicito
        url_m = _YT_URL_RE.search(text)
        if url_m:
            full_url = f"https://www.youtube.com/watch?v={url_m.group(1)}"
            want_transcript = bool(_TRANSCRIPT_RE.search(text))
            return {"action": "info", "url": full_url, "transcript": want_transcript}

        # Ricerca
        search_m = _SEARCH_RE.search(text)
        if search_m:
            query = next((g for g in search_m.groups() if g), "").strip()
            if query:
                return {"action": "search", "query": query}

        return None

    async def run(self, _user_input: str, params: dict) -> str:
        loop = asyncio.get_event_loop()
        if params["action"] == "search":
            return await loop.run_in_executor(None, _search, params["query"])
        else:
            return await loop.run_in_executor(
                None, _info, params["url"], params.get("transcript", False)
            )


# --- implementazioni ---

def _ydl_opts(quiet: bool = True) -> dict:
    return {
        "quiet": quiet,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }


def _fmt_duration(seconds) -> str:
    if not seconds:
        return "?"
    s = int(seconds)
    h, m = divmod(s, 3600)
    m, s = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _fmt_views(views) -> str:
    if views is None:
        return "?"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    if views >= 1_000:
        return f"{views / 1_000:.0f}K"
    return str(views)


def _search(query: str) -> str:
    try:
        import yt_dlp

        opts = {**_ydl_opts(), "extract_flat": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            data = ydl.extract_info(f"ytsearch5:{query}", download=False)

        entries = (data or {}).get("entries") or []
        if not entries:
            return f"Nessun risultato YouTube per: {query}"

        lines = [f"[YOUTUBE SEARCH: {query!r}]\n"]
        for i, e in enumerate(entries[:5], 1):
            title    = e.get("title", "?")
            duration = _fmt_duration(e.get("duration"))
            channel  = e.get("uploader") or e.get("channel") or "?"
            vid_id   = e.get("id") or e.get("url", "").split("v=")[-1]
            url      = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "?"
            lines.append(f"{i}. {title}\n   Canale: {channel} | Durata: {duration}\n   {url}")

        return "\n\n".join(lines)

    except ImportError:
        return "yt-dlp non installato. Esegui: pip install yt-dlp"
    except Exception as e:
        return f"Errore ricerca YouTube: {e}"


def _info(url: str, want_transcript: bool) -> str:
    try:
        import yt_dlp

        opts = _ydl_opts()
        if want_transcript:
            opts["writesubtitles"]     = True
            opts["writeautomaticsub"]  = True
            opts["subtitleslangs"]     = ["it", "en"]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return f"Impossibile ottenere info per: {url}"

        title    = info.get("title", "?")
        channel  = info.get("uploader") or info.get("channel") or "?"
        duration = _fmt_duration(info.get("duration"))
        views    = _fmt_views(info.get("view_count"))
        date_raw = info.get("upload_date", "")
        date_str = f"{date_raw[6:8]}/{date_raw[4:6]}/{date_raw[:4]}" if len(date_raw) == 8 else "?"
        desc     = (info.get("description") or "")[:_MAX_DESC]
        if len(info.get("description") or "") > _MAX_DESC:
            desc += "..."

        parts = [
            f"[YOUTUBE: {title}]",
            f"Canale: {channel} | Durata: {duration} | Visualizzazioni: {views} | Data: {date_str}",
            f"URL: {url}",
        ]
        if desc:
            parts.append(f"\nDescrizione:\n{desc}")

        # Trascrizione: cerca nei subtitles automatici
        if want_transcript:
            transcript = _extract_transcript(info)
            if transcript:
                parts.append(f"\nTrascrizione:\n{transcript}")
            else:
                parts.append("\n(Trascrizione non disponibile per questo video)")

        return "\n".join(parts)

    except ImportError:
        return "yt-dlp non installato. Esegui: pip install yt-dlp"
    except Exception as e:
        return f"Errore recupero info YouTube: {e}"


def _extract_transcript(info: dict) -> str:
    """Estrae testo dai sottotitoli automatici se disponibili."""
    subs = info.get("automatic_captions") or info.get("subtitles") or {}

    # Preferisce italiano, poi inglese
    for lang in ("it", "en"):
        entries = subs.get(lang) or []
        for fmt in entries:
            if fmt.get("ext") in ("json3", "srv3", "vtt"):
                # Il testo raw è nel campo 'url' — sarebbe un altro fetch
                # Per ora segnaliamo disponibilità
                return f"(Sottotitoli disponibili in '{lang}' — usa yt-dlp --write-sub per scaricarli)"

    return ""
