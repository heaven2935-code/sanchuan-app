"""使用 FFmpeg 進行混音、轉檔與音量調整，產生伴唱／導唱／純人聲版本。"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from config import MP3_BITRATE

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


def _encode_args(fmt: str, out_path: Path) -> list[str]:
    if fmt == "mp3":
        return ["-c:a", "libmp3lame", "-b:a", MP3_BITRATE, str(out_path)]
    if fmt == "wav":
        return ["-c:a", "pcm_s16le", str(out_path)]
    raise MixError(f"不支援的輸出格式：{fmt}")


def convert_to_wav(src: Path, out_path: Path) -> Path:
    """將任意支援的音訊／影片來源轉為 wav，供後續人聲分離使用。"""
    if not check_ffmpeg_available():
        raise MixError("找不到 FFmpeg，請先安裝並加入系統 PATH")
    args = ["-i", str(src), "-vn", "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(out_path)]
    _run_ffmpeg(args)
    return out_path


def _mix_stems(
    stem_paths: list[Path],
    out_path: Path,
    fmt: str,
    vocals_path: Optional[Path] = None,
    vocal_volume: float = 1.0,
) -> None:
    inputs: list[str] = []
    for p in stem_paths:
        inputs += ["-i", str(p)]

    n = len(stem_paths)
    filter_parts = []

    if vocals_path is not None:
        inputs += ["-i", str(vocals_path)]
        filter_parts.append(f"[{n}:a]volume={vocal_volume}[vfx]")
        labels = "".join(f"[{i}:a]" for i in range(n)) + "[vfx]"
        total_inputs = n + 1
    else:
        labels = "".join(f"[{i}:a]" for i in range(n))
        total_inputs = n

    filter_parts.append(f"{labels}amix=inputs={total_inputs}:duration=longest:normalize=0[mixed]")
    filter_parts.append("[mixed]alimiter=limit=0.95[aout]")
    filter_complex = ";".join(filter_parts)

    args = [*inputs, "-filter_complex", filter_complex, "-map", "[aout]", *_encode_args(fmt, out_path)]
    _run_ffmpeg(args)


def _transcode(src: Path, out_path: Path, fmt: str) -> None:
    args = ["-i", str(src), *_encode_args(fmt, out_path)]
    _run_ffmpeg(args)


def render_outputs(
    stems: dict[str, Path],
    output_dir: Path,
    vocal_volume_percent: float,
    formats: tuple[str, ...] = ("mp3", "wav"),
    progress_callback: Optional[ProgressCallback] = None,
) -> dict[str, Path]:
    """產生純伴唱版、導唱版（依 vocal_volume_percent 調整人聲音量）、純人聲版輸出檔案。"""
    if not check_ffmpeg_available():
        raise MixError("找不到 FFmpeg，請先安裝並加入系統 PATH")
    if not formats:
        raise MixError("請至少選擇一種輸出格式")

    for name in ("vocals", "drums", "bass", "other"):
        if name not in stems:
            raise MixError(f"缺少音軌：{name}")

    output_dir.mkdir(parents=True, exist_ok=True)
    instrumental_stems = [stems["drums"], stems["bass"], stems["other"]]
    vocal_volume = max(0.0, min(1.0, vocal_volume_percent / 100.0))

    steps = [
        ("instrumental", "純伴唱版"),
        ("lead_vocal", "導唱版"),
        ("vocals_only", "純人聲版"),
    ]
    total_steps = len(steps) * len(formats)
    done = 0
    outputs: dict[str, Path] = {}

    for key, label in steps:
        for fmt in formats:
            out_path = output_dir / f"{key}.{fmt}"
            if progress_callback:
                progress_callback(done / total_steps, f"產生{label}（{fmt.upper()}）…")

            if key == "instrumental":
                _mix_stems(instrumental_stems, out_path, fmt)
            elif key == "lead_vocal":
                _mix_stems(
                    instrumental_stems, out_path, fmt,
                    vocals_path=stems["vocals"], vocal_volume=vocal_volume,
                )
            else:  # vocals_only
                _transcode(stems["vocals"], out_path, fmt)

            outputs[f"{key}_{fmt}"] = out_path
            done += 1
            if progress_callback:
                progress_callback(done / total_steps, f"{label}（{fmt.upper()}）完成")

    return outputs
