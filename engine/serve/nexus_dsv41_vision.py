"""NEXUS local: dsv41's own image path (no strata-vision.exe).

The upstream server encodes pictures with `strata-vision` (llama.cpp's mtmd) and hands the engine embeddings; that
binary cannot open a `deepseek41` model ("unknown model architecture"), so images were refused for this engine.

The dsv41 engine takes the pictures themselves instead: `GENI <max_new> [keys] <file> <ids>` reads a DSI1 file of raw
RGB and runs its own vision tower (src/dsv41/ds4_vision.cu).  What must match is only the geometry:

    P = clip.vision.patch_size (14), M = clip.vision.projector.scale_factor (3)
    both sides a multiple of P (the engine refuses anything else)
    n_h = ceil(height / P / M), n_w = ceil(width / P / M)
    tokens = n_h * (n_w + 1) + 2          (image_start, n_h rows of n_w + newline, image_end)

This module does the resize the engine's header calls "the server's resize" and writes the DSI1 file.
"""
from __future__ import annotations

import io
import struct
from pathlib import Path

PATCH = 14          # clip.vision.patch_size
MERGE = 3           # clip.vision.projector.scale_factor
ALIGN = PATCH       # the engine's own requirement is a multiple of P; P*M keeps the grid exact
MIN_PIXELS = 295936         # clip.vision.image_min_pixels
MAX_PIXELS = 1587600        # 1260 x 1260: n_h = n_w = 30 -> 932 image tokens, under the 1024 cap
TOKEN_LIMIT = 1024          # the reader's default cap (server.Vision.DEFAULT_MAX_TOKENS["gpu"])


def _round(value: float, prefer_down: bool) -> int:
    n = int(value) // ALIGN * ALIGN
    if not prefer_down and n < value:
        n += ALIGN
    return max(ALIGN, n)


def fit(width: int, height: int) -> tuple[int, int]:
    """The size the engine is fed: aspect kept, area inside [MIN_PIXELS, MAX_PIXELS], both sides a multiple of PATCH."""
    if width <= 0 or height <= 0:
        raise ValueError("an image with no pixels")
    area = width * height
    scale = 1.0
    if area > MAX_PIXELS:
        scale = (MAX_PIXELS / area) ** 0.5
    elif area < MIN_PIXELS:
        scale = (MIN_PIXELS / area) ** 0.5
    w, h = _round(width * scale, prefer_down=scale < 1), _round(height * scale, prefer_down=scale < 1)
    for _ in range(64):                       # a short side can land under PATCH after the rounding
        if image_tokens(w, h) <= TOKEN_LIMIT and w * h <= MAX_PIXELS and w * h >= MIN_PIXELS:
            break
        w = max(ALIGN, w - ALIGN)
        h = max(ALIGN, h - ALIGN)
    return w, h


def image_tokens(width: int, height: int) -> int:
    if width % PATCH or height % PATCH:
        raise ValueError(f"the engine needs both sides as multiples of {PATCH}, not {width}x{height}")
    gh, gw = height // PATCH, width // PATCH
    n_h = -(-gh // MERGE)
    n_w = -(-gw // MERGE)
    return n_h * (n_w + 1) + 2


def encode(sources: list) -> list[tuple[bytes, int, int, int]]:
    """Every source (a path or bytes) -> (RGB rows, width, height, its image tokens)."""
    from PIL import Image

    out = []
    for src in sources:
        raw = src if isinstance(src, (bytes, bytearray)) else Path(str(src)).read_bytes()
        with Image.open(io.BytesIO(raw)) as im:
            im = im.convert("RGB")
            w, h = fit(im.width, im.height)
            if (w, h) != (im.width, im.height):
                im = im.resize((w, h), Image.LANCZOS)
            out.append((im.tobytes(), w, h, image_tokens(w, h)))
    return out


def write(path: Path, pics: list[tuple[bytes, int, int, int]], starts: list[int]) -> None:
    """DSI1: int32 magic, int32 count, then per picture int64 start, int32 width, int32 height, height*width*3 RGB."""
    with open(path, "wb") as f:
        f.write(b"DSI1")
        f.write(struct.pack("<i", len(pics)))
        for (rgb, w, h, _tokens), start in zip(pics, starts):
            f.write(struct.pack("<qii", int(start), int(w), int(h)))
            f.write(rgb)
