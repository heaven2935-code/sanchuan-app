"""呼叫 Demucs 將音訊分離為 vocals / drums / bass / other 四軌。"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from config import DEMUCS_MODEL, DEMUCS_STEMS

ProgressCallback = Callable[[float, str], None]

_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)%\|")


class SeparationError(Exception):
    """Demucs 人聲分離失敗。"""


def check_demucs_available() -> bool:
    try:
        import demucs  # noqa: F401
        import torch  # noqa: F401
        return True
    except ImportError:
        return False


def separate(
    audio_path: Path,
    stems_dir: Path,
    model: str = DEMUCS_MODEL,
    progress_callback: Optional[ProgressCallback] = None,
) -> dict[str, Path]:
    """執行 Demucs 分離，回傳各音軌檔案路徑（vocals/drums/bass/other）。"""
    if not audio_path.exists():
        raise SeparationError(f"找不到來源音訊檔案：{audio_path}")

    cmd = [
        sys.executable, "-m", "demucs",
        "-n", model,
        "-d", "cpu",
        "-o", str(stems_dir),
        str(audio_path),
    ]

    if progress_callback:
        progress_callback(0.0, "正在載入 Demucs 模型（首次執行需下載，請耐心等候）…")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as exc:
        raise SeparationError("找不到 Python 直譯器或 demucs 套件，請確認安裝是否完成") from exc

    output_lines: list[str] = []
    assert process.stdout is not None
    buffer = ""
    while True:
        ch = process.stdout.read(1)
        if ch == "":
            break
        if ch in ("\n", "\r"):
            line = buffer
            buffer = ""
            if not line:
                continue
            output_lines.append(line)
            match = _PERCENT_RE.search(line)
            if match and progress_callback:
                pct = float(match.group(1)) / 100.0
                progress_callback(pct, "人聲分離中…")
        else:
            buffer += ch
    if buffer:
        output_lines.append(buffer)

    return_code = process.wait()
    if return_code != 0:
        tail = "\n".join(output_lines[-20:]) or "（無詳細輸出）"
        raise SeparationError(f"Demucs 分離失敗（結束碼 {return_code}）：\n{tail}")

    track_name = audio_path.stem
    model_dir = stems_dir / model / track_name
    stems: dict[str, Path] = {}
    for stem in DEMUCS_STEMS:
        stem_path = model_dir / f"{stem}.wav"
        if not stem_path.exists():
            raise SeparationError(f"分離完成但找不到 {stem} 音軌，請檢查 Demucs 輸出目錄：{model_dir}")
        stems[stem] = stem_path

    if progress_callback:
        progress_callback(1.0, "人聲分離完成")
    return stems
