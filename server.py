"""Flower Cutter - local high-precision cutout tool (SAM 2.1 + Grounding DINO)."""

import base64
import io
import re
import threading
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageOps
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)
SAM_CKPT = BASE_DIR / "sam2.1_l.pt"
GD_ID = "IDEA-Research/grounding-dino-base"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
PREVIEW_MAX = 4096
OVERLAY_RGB = (255, 64, 176)


def _log(msg: str) -> None:
    print(f"[flower-cutter] {msg}", flush=True)


_log(f"loading models on {DEVICE} ...")
from ultralytics.models.sam import SAM2Predictor
from transformers import AutoModelForZeroShotObjectDetection, AutoProcessor

_sam = SAM2Predictor(
    overrides=dict(
        model=str(SAM_CKPT) if SAM_CKPT.exists() else "sam2.1_l.pt",
        device=DEVICE,
        verbose=False,
        save=False,
        plots=False,
    )
)
_gd_proc = AutoProcessor.from_pretrained(GD_ID)
_gd = AutoModelForZeroShotObjectDetection.from_pretrained(GD_ID).to(DEVICE).eval()

# warm up
with torch.no_grad():
    _sam.set_image(np.zeros((64, 64, 3), dtype=np.uint8))
    _sam(points=[[[32, 32]]], labels=[[1]])
_log("models ready")

LOCK = threading.Lock()


class State:
    def __init__(self) -> None:
        self.bgr: np.ndarray | None = None
        self.rgb: np.ndarray | None = None
        self.stem = "image"
        self.preview_jpeg = b""
        self.iw = self.ih = 0
        self.pw = self.ph = 0
        self.masks: dict[str, tuple[np.ndarray, int, int]] = {}

    @property
    def preview_scale(self) -> float:
        return self.pw / self.iw if self.iw else 1.0


state = State()
app = FastAPI(title="Vyrezchik")


# ---------- helpers ----------

def _store_mask(mask: np.ndarray) -> str:
    mid = uuid.uuid4().hex[:12]
    h, w = mask.shape
    state.masks[mid] = (np.packbits(mask), h, w)
    return mid


def _load_mask(mid: str) -> np.ndarray:
    packed, h, w = state.masks[mid]
    return np.unpackbits(packed, count=h * w).reshape(h, w).astype(bool)


def _mask_bbox(mask: np.ndarray) -> list[int]:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return [0, 0, 0, 0]
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def _mask_png_uri(mask: np.ndarray) -> str:
    """Colored RGBA overlay PNG (preview scale) as data URI."""
    s = state.preview_scale
    if s != 1.0:
        m = cv2.resize(
            mask.astype(np.uint8),
            (state.pw, state.ph),
            interpolation=cv2.INTER_NEAREST,
        ).astype(bool)
    else:
        m = mask
    rgba = np.zeros((m.shape[0], m.shape[1], 4), dtype=np.uint8)
    rgba[m] = (*OVERLAY_RGB, 255)
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _sanitize(name: str, fallback: str = "object") -> str:
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name).strip(" .")
    return (name[:80] or fallback)


def _iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    ua = (ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - inter
    return inter / ua if ua > 0 else 0.0


def _nms(boxes: np.ndarray, scores: np.ndarray, thr=0.6, limit=24) -> list[int]:
    keep: list[int] = []
    for i in np.argsort(-scores):
        if len(keep) >= limit:
            break
        if all(_iou(boxes[i], boxes[j]) <= thr for j in keep):
            keep.append(int(i))
    return keep


# ---------- API ----------

class SegmentReq(BaseModel):
    points: list[list[int]]  # [[x, y, label], ...] label: 1=include, 0=exclude


class DetectReq(BaseModel):
    text: str
    threshold: float = 0.2


class ObjectItem(BaseModel):
    mask_id: str
    name: str


class ExportReq(BaseModel):
    items: list[ObjectItem]
    mode: str = "each"  # "each" | "union"
    union_name: str = "combined"
    background: str = "transparent"  # "transparent" | "white"
    padding: int = 0
    feather: int = 0


class FolderReq(BaseModel):
    path: str


@app.post("/api/open")
def open_image(file: UploadFile = File(...)):
    raw = file.file.read()
    try:
        pil = Image.open(io.BytesIO(raw))
        pil = ImageOps.exif_transpose(pil).convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"画像を読み込めません: {e}")
    stem = Path(file.filename or "image").stem

    w, h = pil.size
    scale = min(1.0, PREVIEW_MAX / max(w, h))
    if scale < 1.0:
        prev = pil.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    else:
        prev = pil
    buf = io.BytesIO()
    prev.save(buf, format="JPEG", quality=88)

    rgb = np.array(pil)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    with LOCK:
        t0 = time.time()
        _sam.set_image(bgr)
        elapsed = time.time() - t0
        state.bgr = bgr
        state.rgb = rgb
        state.stem = _sanitize(stem, "image")
        state.preview_jpeg = buf.getvalue()
        state.iw, state.ih = w, h
        state.pw, state.ph = prev.size
        state.masks = {}

    return {
        "width": w,
        "height": h,
        "preview_w": state.pw,
        "preview_h": state.ph,
        "stem": state.stem,
        "encode_ms": int(elapsed * 1000),
        "preview": "data:image/jpeg;base64," + base64.b64encode(state.preview_jpeg).decode(),
    }


@app.post("/api/segment")
def segment(req: SegmentReq):
    if state.bgr is None:
        raise HTTPException(400, "先に画像を開いてください")
    pts = [p for p in req.points if len(p) == 3]
    if not pts:
        raise HTTPException(400, "ポイントがありません")
    coords = [[int(p[0]), int(p[1])] for p in pts]
    labels = [[int(p[2]) for p in pts]]

    with LOCK:
        t0 = time.time()
        r = _sam(points=[coords], labels=labels)
        elapsed = time.time() - t0
        masks = r[0].masks
        if masks is None or len(masks.data) == 0:
            return {"mask_id": None, "png": None, "elapsed_ms": int(elapsed * 1000)}
        m = masks.data[0].cpu().numpy().astype(bool)
        mid = _store_mask(m)
        png = _mask_png_uri(m)

    return {
        "mask_id": mid,
        "area": int(m.sum()),
        "bbox": _mask_bbox(m),
        "png": png,
        "elapsed_ms": int(elapsed * 1000),
    }


@app.post("/api/detect")
def detect(req: DetectReq):
    if state.bgr is None:
        raise HTTPException(400, "先に画像を開いてください")
    text = req.text.strip()
    if not text:
        raise HTTPException(400, "テキストを入力してください")

    pil = Image.fromarray(state.rgb)
    with LOCK:
        t0 = time.time()
        inputs = _gd_proc(images=pil, text=text, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            outputs = _gd(**inputs)
        res = _gd_proc.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=float(req.threshold),
            text_threshold=0.24,
            target_sizes=[(state.ih, state.iw)],
        )[0]
        boxes = res["boxes"].cpu().numpy()
        scores = res["scores"].cpu().numpy()
        raw_labels = [str(t) for t in res["text_labels"]] if "text_labels" in res else []
        labels = [t.strip() or text for t in raw_labels] or [text] * len(boxes)
        keep = _nms(boxes, scores)
        if not keep:
            return {"detections": [], "elapsed_ms": int((time.time() - t0) * 1000)}
        kept_boxes = boxes[keep].tolist()
        r = _sam(bboxes=kept_boxes)
        elapsed = time.time() - t0
        masks = r[0].masks
        out = []
        if masks is not None:
            md = masks.data.cpu().numpy().astype(bool)
            for i, bi in enumerate(keep):
                if i >= len(md):
                    break
                m = md[i]
                out.append(
                    {
                        "mask_id": _store_mask(m),
                        "score": round(float(scores[bi]), 3),
                        "label": labels[bi] if bi < len(labels) else text,
                        "bbox": _mask_bbox(m),
                        "area": int(m.sum()),
                        "png": _mask_png_uri(m),
                    }
                )
    return {"detections": out, "elapsed_ms": int(elapsed * 1000)}


@app.post("/api/export")
def export(req: ExportReq):
    if state.rgb is None:
        raise HTTPException(400, "先に画像を開いてください")
    if not req.items:
        raise HTTPException(400, "書き出すオブジェクトがありません")
    for it in req.items:
        if it.mask_id not in state.masks:
            raise HTTPException(400, f"マスクが見つかりません: {it.mask_id}")
    if req.mode not in ("each", "union"):
        raise HTTPException(400, "mode は each か union です")
    if req.background not in ("transparent", "white"):
        raise HTTPException(400, "background は transparent か white です")
    pad = max(0, min(200, int(req.padding)))
    feather = max(0, min(5, int(req.feather)))

    out_dir = EXPORT_DIR / state.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    used: set[str] = set()

    def unique_name(name: str) -> str:
        base = _sanitize(name)
        cand, n = base, 1
        while cand in used:
            n += 1
            cand = f"{base}-{n}"
        used.add(cand)
        return cand

    def save(mask: np.ndarray, name: str) -> str:
        x1, y1, x2, y2 = _mask_bbox(mask)
        if x2 <= x1 or y2 <= y1:
            raise HTTPException(400, f"空のマスクです: {name}")
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(state.iw - 1, x2 + pad)
        y2 = min(state.ih - 1, y2 + pad)
        alpha = (mask[y1 : y2 + 1, x1 : x2 + 1] * 255).astype(np.uint8)
        if feather > 0:
            k = feather * 2 + 1
            alpha = cv2.GaussianBlur(alpha, (k, k), 0)
        rgb = state.rgb[y1 : y2 + 1, x1 : x2 + 1]
        path = out_dir / f"{unique_name(name)}.png"
        if req.background == "white":
            a = alpha.astype(np.float32) / 255.0
            out = (rgb.astype(np.float32) * a[..., None] + 255.0 * (1.0 - a[..., None])).astype(np.uint8)
            Image.fromarray(out).save(path)
        else:
            rgba = np.dstack([rgb, alpha])
            Image.fromarray(rgba, mode="RGBA").save(path)
        files.append(str(path))
        return str(path)

    with LOCK:
        if req.mode == "union":
            acc = np.zeros((state.ih, state.iw), dtype=bool)
            for it in req.items:
                acc |= _load_mask(it.mask_id)
            save(acc, req.union_name)
        else:
            for it in req.items:
                save(_load_mask(it.mask_id), it.name)

    return {"dir": str(out_dir), "files": files}


@app.post("/api/open_folder")
def open_folder(req: FolderReq):
    import os

    p = Path(req.path).resolve()
    if not str(p).startswith(str(EXPORT_DIR.resolve())):
        raise HTTPException(400, "許可されていないパスです")
    if not p.exists():
        raise HTTPException(404, "フォルダがありません")
    os.startfile(str(p))  # Windows
    return {"ok": True}


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


if __name__ == "__main__":
    import os
    import threading
    import webbrowser

    import uvicorn

    port = 8765
    if not os.environ.get("FLOWER_CUTTER_NO_BROWSER"):
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
