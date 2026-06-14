from datetime import datetime
from pathlib import Path

_CONST_DIR = Path(__file__).parent.parent / "constitution"


def build_system_prompt() -> str:
    def _read(name: str) -> str:
        p = _CONST_DIR / name
        return p.read_text(encoding="utf-8") if p.exists() else ""

    ari = _read("ari.md")
    roby = _read("roby.md")
    now = datetime.now().strftime("%A %d %B %Y, %H:%M")

    return f"""{ari}

---

{roby}

---

Data e ora corrente: {now}""".strip()
