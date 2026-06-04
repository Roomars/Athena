#!/usr/bin/env python3
"""
Genera i PNG necessari per Tauri a partire dagli SVG sorgente.
Ordine tentativi: cairosvg → rsvg-convert → Pillow → stdlib puro
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SVG_APP  = ROOT / "static/icons/athena-app.svg"
SVG_TRAY = ROOT / "static/icons/athena-menubar.svg"
OUT_APP  = ROOT / "src-tauri/icons/app-icon.png"
OUT_TRAY = ROOT / "src-tauri/icons/tray-icon.png"


def try_cairosvg(src: Path, dst: Path, size: int) -> bool:
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=str(src), write_to=str(dst),
                         output_width=size, output_height=size)
        return True
    except Exception:
        return False


def try_rsvg(src: Path, dst: Path, size: int) -> bool:
    try:
        r = subprocess.run(
            ["rsvg-convert", "-w", str(size), "-h", str(size),
             "-o", str(dst), str(src)],
            capture_output=True,
        )
        return r.returncode == 0
    except FileNotFoundError:
        return False


def pillow_app_icon(dst: Path, size: int) -> bool:
    """Bronze rounded-square app icon with a simplified helmet drawn in white."""
    try:
        from PIL import Image, ImageDraw, ImageFilter  # type: ignore

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded bronze background
        r = size // 5
        bronze = (196, 151, 58, 255)
        draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill=bronze)

        # Helmet proportions (scaled from 0-24 viewBox to `size` pixels)
        s = size / 24.0
        white = (255, 255, 255, 242)
        bg    = (196, 151, 58, 255)

        # Outer dome: rounded rectangle standing in for the dome shape
        mx, my = size // 2, size // 2
        hw = int(10 * s)   # half-width
        ht = int(11 * s)   # half-height
        dr = int(4 * s)    # dome corner radius
        draw.rounded_rectangle(
            [mx - hw, my - ht, mx + hw, my + ht], radius=dr, fill=white
        )

        # Left chin flap (bottom-left lobe)
        fw = int(4 * s)
        fh = int(2 * s)
        fy = my + ht - fh
        draw.rectangle([mx - hw, fy, mx - int(1 * s), fy + fh * 2], fill=white)

        # Right chin flap
        draw.rectangle([mx + int(1 * s), fy, mx + hw, fy + fh * 2], fill=white)

        # Left eye slot (punched out)
        ew = int(4.5 * s)
        eh = int(1.2 * s)
        ey = my - int(1 * s)
        draw.rounded_rectangle(
            [mx - hw + int(0.5 * s), ey, mx - int(1.2 * s), ey + eh],
            radius=int(eh * 0.4), fill=bg
        )

        # Right eye slot
        draw.rounded_rectangle(
            [mx + int(1.2 * s), ey, mx + hw - int(0.5 * s), ey + eh],
            radius=int(eh * 0.4), fill=bg
        )

        img.save(str(dst))
        return True
    except ImportError:
        return False


def pillow_tray_icon(dst: Path, size: int) -> bool:
    """Black helmet on transparent background for macOS template icon."""
    try:
        from PIL import Image, ImageDraw  # type: ignore

        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        black = (0, 0, 0, 255)
        s = size / 24.0

        mx, my = size // 2, size // 2
        hw = int(9.5 * s)
        ht = int(10 * s)
        dr = int(3.5 * s)
        draw.rounded_rectangle(
            [mx - hw, my - ht, mx + hw, my + ht], radius=dr, fill=black
        )

        # Chin flaps
        fy = my + ht - int(1.5 * s)
        draw.rectangle([mx - hw, fy, mx - int(1 * s), my + ht + int(1.5 * s)], fill=black)
        draw.rectangle([mx + int(1 * s), fy, mx + hw, my + ht + int(1.5 * s)], fill=black)

        # Eye slots (transparent)
        ew = int(4 * s)
        eh = int(1.1 * s)
        ey = my - int(0.8 * s)
        transp = (0, 0, 0, 0)
        draw.rounded_rectangle(
            [mx - hw + int(0.5 * s), ey, mx - int(1.2 * s), ey + eh],
            radius=int(eh * 0.4), fill=transp
        )
        draw.rounded_rectangle(
            [mx + int(1.2 * s), ey, mx + hw - int(0.5 * s), ey + eh],
            radius=int(eh * 0.4), fill=transp
        )

        img.save(str(dst))
        return True
    except ImportError:
        return False


def stdlib_png(dst: Path, size: int, rgb: tuple) -> bool:
    """Minimal solid-colour PNG using only stdlib (last resort)."""
    import struct, zlib
    r, g, b = rgb

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    row = b"\x00" + bytes([r, g, b] * size)
    compressed = zlib.compress(row * size)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", compressed)
        + chunk(b"IEND", b"")
    )
    dst.write_bytes(png)
    return True


def copy_png(src_png: Path, dst: Path) -> bool:
    """Usa direttamente il PNG sorgente se esiste."""
    if src_png.exists() and src_png.stat().st_size > 10_000:
        import shutil
        shutil.copy2(src_png, dst)
        return True
    return False


def generate_app(src: Path, dst: Path):
    size = 512
    name = dst.name
    # Usa athena-app.png se esiste (priorità massima — è l'icona vera di Roby)
    src_png = src.parent / (src.stem + ".png")
    methods = [
        ("PNG esistente",  lambda: copy_png(src_png, dst)),
        ("cairosvg",       lambda: try_cairosvg(src, dst, size)),
        ("rsvg-convert",   lambda: try_rsvg(src, dst, size)),
        ("Pillow",         lambda: pillow_app_icon(dst, size)),
        ("stdlib",         lambda: stdlib_png(dst, size, (196, 151, 58))),
    ]
    for label, fn in methods:
        if fn():
            print(f"  ✓ {name} ({size}px) — via {label}")
            return
    print(f"  ✗ {name}: tutti i metodi falliti", file=sys.stderr)
    sys.exit(1)


def generate_tray(src: Path, dst: Path):
    size = 44
    name = dst.name
    methods = [
        ("cairosvg",       lambda: try_cairosvg(src, dst, size)),
        ("rsvg-convert",   lambda: try_rsvg(src, dst, size)),
        ("Pillow",         lambda: pillow_tray_icon(dst, size)),
        ("stdlib",         lambda: stdlib_png(dst, size, (0, 0, 0))),
    ]
    for label, fn in methods:
        if fn():
            print(f"  ✓ {name} ({size}px) — via {label}")
            return
    print(f"  ✗ {name}: tutti i metodi falliti", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    print("→ Generazione icone PNG…")
    generate_app(SVG_APP, OUT_APP)
    generate_tray(SVG_TRAY, OUT_TRAY)
    print("  Fatto.")
