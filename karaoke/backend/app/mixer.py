"""使用 FFmpeg 混音與轉檔，產生原唱／伴奏／人聲三軌供前端即時混音播放。"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from .config import MP3_BITRATE

ProgressCallback = Callable[[float, str], None]


class MixError(Exception):
    """FFmpeg 混音或轉檔失敗。"""


def check_ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MixError("找不到 FFmpeg，請先安裝並加入系統 PATH") from exc
    if result.returncode != 0:
        raise MixError(f"FFmpeg 執行失敗：{result.stderr.strip()[-800:]}")


def _transcode(src: Path, out_path: Path) -> None:
    _run_ffmpeg(["-i", str(src), "-c:a", "libmp3lame", "-b:a", MP3_BITRATE, str(out_path)])


def _mix_instrumental(stem_paths: list[Path], out_path: Path) -> None:
    inputs: list[str] = []
    for p in stem_paths:
        inputs += ["-i", str(p)]
    n = len(stem_paths)
    labels = "".join(f"[{i}:a]" for i in range(n))
    filter_complex = (
        f"{labels}amix=inputs={n}:duration=longest:normalize=0[mixed];"
        "[mixed]alimiter=limit=0.95[aout]"
    )
    args = [*inputs, "-filter_complex", filter_complex, "-map", "[aout]",
            "-c:a", "libmp3lame", "-b:a", MP3_BITRATE, str(out_path)]
    _run_ffmpeg(args)


def probe_duration(path: Path) -> float:
    """取得音訊長度（秒）。"""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MixError("找不到 FFprobe，請先安裝 FFmpeg 並加入系統 PATH") from exc
    if result.returncode != 0 or not result.stdout.strip():
        raise MixError(f"無法取得音訊長度：{result.stderr.strip()[-400:]}")
    return float(result.stdout.strip())


def render_tracks(
    source_audio: Path,
    stems: dict[str, Path],
    output_dir: Path,
    progress_callback: Optional[ProgressCallback] = None,
) -> dict[str, Path]:
    """產生 original / instrumental / vocals 三軌 MP3，回傳各檔案路徑。"""
    if not check_ffmpeg_available():
        raise MixError("找不到 FFmpeg，請先安裝並加入系統 PATH")
    for name in ("vocals", "drums", "bass", "other"):
        if name not in stems:
            raise MixError(f"缺少音軌：{name}")

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    steps = [
        ("original", "原唱"),
        ("instrumental", "伴奏"),
        ("vocals", "人聲"),
    ]
    total = len(steps)
    for i, (key, label) in enumerate(steps):
        if progress_callback:
            progress_callback(i / total, f"產生{label}軌…")
        out_path = output_dir / f"{key}.mp3"
        if key == "original":
            _transcode(source_audio, out_path)
        elif key == "instrumental":
            _mix_instrumental([stems["drums"], stems["bass"], stems["other"]], out_path)
        else:  # vocals
            _transcode(stems["vocals"], out_path)
        outputs[key] = out_path

    if progress_callback:
        progress_callback(1.0, "混音完成")
    return outputs
