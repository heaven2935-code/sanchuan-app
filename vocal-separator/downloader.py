"""使用 yt-dlp 從影音網址擷取音訊。

本模組僅下載一般公開、未受保護的內容。不會、也不允許使用任何登入憑證、
Cookie 或付費會員資訊來繞過網站的 DRM、付費牆或登入限制；偵測到此類
受限內容時一律拒絕下載。
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import yt_dlp

ProgressCallback = Callable[[float, str], None]

# 錯誤訊息中出現以下關鍵字，視為內容受登入 / 付費牆 / DRM 等限制保護
_RESTRICTED_MARKERS = (
    "sign in", "log in", "login required", "premium", "purchase",
    "private video", "members-only", "members only", "subscriber",
    "this video is unavailable", "drm", "paywall", "requires payment",
    "age-restricted", "confirm your age", "geo-restricted",
    "not available in your country", "join this channel",
)


class DownloadError(Exception):
    """音訊下載失敗（含網路錯誤）。"""


class RestrictedContentError(DownloadError):
    """內容受 DRM、付費牆或登入限制保護，本工具拒絕嘗試繞過。"""


def check_ytdlp_available() -> bool:
    try:
        import yt_dlp  # noqa: F401
        return True
    except ImportError:
        return False


def _looks_restricted(message: str) -> bool:
    lower = message.lower()
    return any(marker in lower for marker in _RESTRICTED_MARKERS)


class _SilentLogger:
    """壓制 yt-dlp 直接印到終端機的訊息，錯誤改由呼叫端以例外處理。"""

    def debug(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        pass


def _make_hook(progress_callback: Optional[ProgressCallback]):
    def hook(d: dict) -> None:
        if progress_callback is None:
            return
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            fraction = (downloaded / total) if total else 0.0
            progress_callback(min(fraction, 1.0), f"下載中… {downloaded // 1024} KB")
        elif status == "finished":
            progress_callback(1.0, "下載完成，轉換音訊格式中…")
    return hook


def download_audio(
    url: str,
    input_dir: Path,
    progress_callback: Optional[ProgressCallback] = None,
) -> Path:
    """下載網址中的音訊並轉存為 wav，回傳檔案路徑。

    僅使用公開存取方式，不附帶任何登入或付費憑證。
    """
    if not url or not url.strip():
        raise DownloadError("請輸入有效的影音網址")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(input_dir / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "logger": _SilentLogger(),
        "progress_hooks": [_make_hook(progress_callback)],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as exc:
        message = str(exc)
        if _looks_restricted(message):
            raise RestrictedContentError(
                "此內容受登入、付費會員或 DRM 保護，本工具依政策拒絕繞過，無法下載。"
            ) from exc
        raise DownloadError(f"下載失敗：{message}") from exc
    except Exception as exc:  # noqa: BLE001 涵蓋網路逾時等未預期錯誤
        raise DownloadError(f"下載時發生未預期錯誤：{exc}") from exc

    video_id = info.get("id") if isinstance(info, dict) else None
    wav_path = input_dir / f"{video_id}.wav" if video_id else None
    if wav_path is None or not wav_path.exists():
        candidates = sorted(input_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            wav_path = candidates[0]
        else:
            raise DownloadError("下載完成但找不到輸出的音訊檔案")
    return wav_path
