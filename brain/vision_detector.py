"""
VisionDetector — YOLO object detection su screenshot con supervision zones.

Pipeline:
  image_b64 → PIL Image → YOLOv8-nano (MPS) → sv.Detections
           → {objects, zones, counts} JSON

Usato come contesto rapido (~50ms) prima di Gemma per ridurre allucinazioni
e abilitare query strutturate ("quante persone", "c'è qualcosa di anomalo").
"""
import base64
import io
import logging
import threading
from collections import Counter

log = logging.getLogger("vision_detector")

_yolo    = None
_sv_lock = threading.Lock()
_loading = False

# YOLOv8-nano: ~6MB, scaricato in ~/.cache/ultralytics alla prima run
_MODEL_NAME = "yolov8n.pt"

# Quadranti schermo: nomi zone per zone analysis
_ZONES = ["top-left", "top-right", "bottom-left", "bottom-right", "center"]


def _load() -> bool:
    global _yolo, _loading
    with _sv_lock:
        if _yolo is not None:
            return True
        if _loading:
            return False
        _loading = True

    try:
        import torch
        # Blocca MPS PRIMA che ultralytics/YOLO auto-rilevi il device.
        # MLX già occupa Metal esclusivamente — doppio accesso causerebbe "no stream gpu N".
        torch.backends.mps.is_available = lambda: False  # monkeypatch permanente per questo processo

        from ultralytics import YOLO
        device = "cpu"
        model  = YOLO(_MODEL_NAME)
        model.to(device)
        with _sv_lock:
            _yolo    = model
            _loading = False
        log.info("YOLO pronto su cpu (MLX occupa Metal)")
        return True
    except Exception as e:
        log.error(f"Errore caricamento YOLO: {e}")
        with _sv_lock:
            _loading = False
        return False


def is_ready() -> bool:
    return _yolo is not None


def detect(image_b64: str, conf_threshold: float = 0.35) -> dict:
    """
    Esegue YOLO detection su image_b64 e restituisce:
    {
      "objects":   [{"label": str, "confidence": float, "bbox": [x1,y1,x2,y2]}],
      "counts":    {"person": 2, "laptop": 1, ...},
      "zones":     {"top-left": ["laptop"], "center": ["person"], ...},
      "anomalies": []   # oggetti inattesi (bassa confidence o inusuali)
    }
    Ritorna dict vuoto se YOLO non disponibile.
    """
    if not _load():
        return {}

    try:
        from PIL import Image
        image_data = base64.b64decode(image_b64)
        img        = Image.open(io.BytesIO(image_data)).convert("RGB")
        W, H       = img.size
    except Exception as e:
        log.error(f"Errore decodifica immagine detector: {e}")
        return {}

    try:
        results = _yolo(img, conf=conf_threshold, verbose=False)
        boxes   = results[0].boxes

        objects   = []
        label_pos = []  # (label, cx, cy) per zone analysis

        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf  = float(box.conf[0])
            cls   = int(box.cls[0])
            label = _yolo.names[cls]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            objects.append({
                "label":      label,
                "confidence": round(conf, 2),
                "bbox":       [round(x1), round(y1), round(x2), round(y2)],
            })
            label_pos.append((label, cx, cy))

        counts = dict(Counter(o["label"] for o in objects))
        zones  = _assign_zones(label_pos, W, H)

        # Anomalie: oggetti con confidence < 0.45 o categorie inattese su schermo
        _expected_on_screen = {
            "laptop", "keyboard", "mouse", "book", "cell phone", "monitor",
            "person", "cup", "bottle", "chair", "desk",
        }
        anomalies = [
            o["label"] for o in objects
            if o["confidence"] < 0.45 or o["label"] not in _expected_on_screen
        ]

        return {
            "objects":   objects,
            "counts":    counts,
            "zones":     zones,
            "anomalies": list(set(anomalies)),
        }

    except Exception as e:
        log.error(f"Errore YOLO inference: {e}")
        return {}


def _assign_zones(
    label_pos: list[tuple[str, float, float]], W: float, H: float
) -> dict[str, list[str]]:
    """Assegna ogni oggetto rilevato a un quadrante dello schermo."""
    zones: dict[str, list[str]] = {z: [] for z in _ZONES}
    cx_mid, cy_mid = W / 2, H / 2
    margin = 0.15  # margine attorno al centro per la zona "center"

    for label, cx, cy in label_pos:
        in_cx = abs(cx - cx_mid) < W * margin
        in_cy = abs(cy - cy_mid) < H * margin
        if in_cx and in_cy:
            zones["center"].append(label)
        elif cx < cx_mid and cy < cy_mid:
            zones["top-left"].append(label)
        elif cx >= cx_mid and cy < cy_mid:
            zones["top-right"].append(label)
        elif cx < cx_mid and cy >= cy_mid:
            zones["bottom-left"].append(label)
        else:
            zones["bottom-right"].append(label)

    return {k: v for k, v in zones.items() if v}


def detection_to_context(det: dict) -> str:
    """Serializza i risultati YOLO in una stringa compatta per il prompt Gemma."""
    if not det:
        return ""
    lines = []
    if det.get("counts"):
        counts_str = ", ".join(f"{v}× {k}" for k, v in det["counts"].items())
        lines.append(f"Oggetti rilevati: {counts_str}")
    if det.get("zones"):
        for zone, labels in det["zones"].items():
            lines.append(f"  Zona {zone}: {', '.join(labels)}")
    if det.get("anomalies"):
        lines.append(f"Potenziali anomalie: {', '.join(det['anomalies'])}")
    return "\n".join(lines)
