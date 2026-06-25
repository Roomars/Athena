"""
Skill: analizza file binari e strutturati — PDF, CSV/Excel, Word, immagini, audio.
Trigger: path con estensione supportata nel testo dell'utente.
"""
import asyncio
import base64
import logging
import os
import re
from pathlib import Path

from ._base import Skill

log = logging.getLogger("skill.file_processor")

_EXTS = (
    'pdf',
    'csv', 'xlsx', 'xls',
    'docx', 'doc',
    'jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp',
    'mp3', 'wav', 'm4a', 'ogg', 'aac',
)

_EXT_PAT = '|'.join(_EXTS)

# Matcha path assoluti (~/…, /…), relativi (./…) o semplici nomi file
_FILE_RE = re.compile(
    r'([~./\w][\w.\-/]*\.(?:' + _EXT_PAT + r'))',
    re.I,
)

_MAX_CHARS = 6000

_whisper_cache = None


class FileProcessorSkill(Skill):
    name        = "file_processor"
    description = "Analizza file: PDF, CSV/Excel, Word, immagini, audio."

    def match(self, text: str) -> dict | None:
        m = _FILE_RE.search(text)
        if m:
            raw = m.group(1)
            ext = Path(raw).suffix.lower().lstrip('.')
            if ext in _EXTS:
                return {"path": raw, "ext": ext}
        return None

    async def run(self, user_input: str, params: dict) -> str:
        path = Path(os.path.expanduser(params["path"])).resolve()
        ext  = params["ext"]

        if not path.exists():
            return f"File non trovato: {path}"
        size_mb = path.stat().st_size / 1_000_000
        if size_mb > 200:
            return f"File troppo grande ({size_mb:.0f} MB) — non posso elaborarlo."

        loop = asyncio.get_event_loop()

        if ext == 'pdf':
            return await loop.run_in_executor(None, _read_pdf, path)
        elif ext in ('csv', 'xlsx', 'xls'):
            return await loop.run_in_executor(None, _read_tabular, path, ext)
        elif ext in ('docx', 'doc'):
            return await loop.run_in_executor(None, _read_docx, path)
        elif ext in ('jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp'):
            return await _read_image(path, user_input)
        elif ext in ('mp3', 'wav', 'm4a', 'ogg', 'aac'):
            return await loop.run_in_executor(None, _read_audio, path)

        return f"Formato .{ext} non supportato."


# --- estrattori ---

def _read_pdf(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError:
        return "pdfplumber non installato. Esegui: pip install pdfplumber"

    try:
        with pdfplumber.open(path) as pdf:
            n_pages = len(pdf.pages)
            chunks = []
            total = 0
            for page in pdf.pages:
                t = (page.extract_text() or "").strip()
                if not t:
                    continue
                chunks.append(t)
                total += len(t)
                if total >= _MAX_CHARS:
                    break

            body = "\n\n".join(chunks)
            if len(body) > _MAX_CHARS:
                body = body[:_MAX_CHARS] + f"\n\n[... troncato. Pagine totali: {n_pages}]"

            return f"[PDF: {path.name} — {n_pages} pagine]\n\n{body}"
    except Exception as e:
        return f"Errore lettura PDF {path.name}: {e}"


def _read_tabular(path: Path, ext: str) -> str:
    try:
        import pandas as pd
    except ImportError:
        return "pandas non installato. Esegui: pip install pandas openpyxl"

    try:
        if ext == 'csv':
            df = pd.read_csv(path, sep=None, engine='python', nrows=500)
        else:
            df = pd.read_excel(path, nrows=500)

        rows, cols = df.shape
        col_names = ", ".join(str(c) for c in df.columns)

        stat_lines = []
        for col in df.select_dtypes(include='number').columns[:6]:
            s = df[col].describe()
            stat_lines.append(
                f"  {col}: min={s['min']:.2f}  max={s['max']:.2f}  media={s['mean']:.2f}"
            )

        preview = df.head(10).to_string(index=False, max_cols=10)
        if len(preview) > 2000:
            preview = preview[:2000] + "\n[...]"

        parts = [
            f"[{ext.upper()}: {path.name} — {rows} righe × {cols} colonne]",
            f"Colonne: {col_names}",
        ]
        if stat_lines:
            parts.append("Statistiche:\n" + "\n".join(stat_lines))
        parts.append(f"Prime 10 righe:\n{preview}")

        return "\n\n".join(parts)
    except Exception as e:
        return f"Errore lettura file tabellare {path.name}: {e}"


def _read_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        return "python-docx non installato. Esegui: pip install python-docx"

    try:
        doc = Document(path)
        paras = [p.text for p in doc.paragraphs if p.text.strip()]
        body = "\n\n".join(paras)
        if len(body) > _MAX_CHARS:
            body = body[:_MAX_CHARS] + f"\n\n[... troncato a {_MAX_CHARS} caratteri]"
        return f"[DOCX: {path.name} — {len(paras)} paragrafi]\n\n{body}"
    except Exception as e:
        return f"Errore lettura DOCX {path.name}: {e}"


async def _read_image(path: Path, user_input: str) -> str:
    try:
        from .. import vision

        img_b64 = base64.b64encode(path.read_bytes()).decode()
        prompt  = f"Analizza questa immagine in dettaglio. Domanda dell'utente: {user_input}"
        result  = await vision.analyze(img_b64, prompt)
        return f"[IMMAGINE: {path.name}]\n\n{result}"
    except Exception as e:
        return f"Errore analisi immagine {path.name}: {e}"


def _read_audio(path: Path) -> str:
    global _whisper_cache
    try:
        import whisper
    except ImportError:
        return (
            "openai-whisper non installato.\n"
            "Esegui: pip install openai-whisper\n"
            "(~150 MB per il modello base)"
        )

    try:
        if _whisper_cache is None:
            log.info("Caricamento modello Whisper base...")
            _whisper_cache = whisper.load_model("base")

        log.info(f"Trascrizione: {path.name}")
        result = _whisper_cache.transcribe(str(path))
        text   = result.get("text", "").strip()
        lang   = result.get("language", "?")

        if len(text) > _MAX_CHARS:
            text = text[:_MAX_CHARS] + "\n[... troncato]"

        return f"[AUDIO: {path.name} — lingua: {lang}]\n\nTrascrizione:\n{text}"
    except Exception as e:
        return f"Errore trascrizione {path.name}: {e}"
