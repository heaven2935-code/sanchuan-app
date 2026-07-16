"""全域設定常數。"""
from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
CACHE_ROOT = BACKEND_ROOT / "data" / "cache"

DEMUCS_MODEL = "htdemucs"
DEMUCS_STEMS = ("vocals", "drums", "bass", "other")

MP3_BITRATE = "192k"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
