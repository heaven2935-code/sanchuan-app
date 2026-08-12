"""全域設定常數。"""
from __future__ import annotations

import tempfile
from pathlib import Path

APP_NAME = "音樂人聲分離工具"

# 每個工作使用系統暫存目錄下的獨立子資料夾
JOBS_ROOT = Path(tempfile.gettempdir()) / "vocal_separator_jobs"

DEMUCS_MODEL = "htdemucs"
DEMUCS_STEMS = ("vocals", "drums", "bass", "other")

DEFAULT_VOCAL_VOLUME_PERCENT = 20
MP3_BITRATE = "320k"

SUPPORTED_UPLOAD_EXTS = (".mp3", ".wav", ".m4a", ".mp4")
OUTPUT_FORMATS = ("mp3", "wav")
