"""全域設定常數。可用環境變數覆寫，方便部署到不同主機時調整。"""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent

# CACHE_DIR：快取/工作資料存放目錄，容器部署時可指向掛載的持久化磁碟。
CACHE_ROOT = Path(os.environ.get("CACHE_DIR", str(BACKEND_ROOT / "data" / "cache")))

DEMUCS_MODEL = "htdemucs"
DEMUCS_STEMS = ("vocals", "drums", "bass", "other")

MP3_BITRATE = "192k"

# CORS_ORIGINS：允許呼叫此 API 的前端網域，逗號分隔（例如正式前端網址）。
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
