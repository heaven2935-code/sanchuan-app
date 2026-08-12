"""使用 yt-dlp 解析歌曲網址、下載音訊與擷取中繼資料（歌名／歌手／封面）。

僅下載一般公開、未受保護的內容。不會、也不允許使用任何登入憑證、Cookie
或付費會員資訊來繞過網站的 DRM、付費牆或登入限制；偵測到此類受限內容時
一律拒絕下載。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import yt_dlp

ProgressCallback = Callable[[float, str], None]

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


@dataclass
class SongMeta:
    video_id: str
    title: str
    artist: str
    duration: Optional[float]
    thumbnail_url: Optional[str]


@dataclass
class DownloadedSong:
    meta: SongMeta
    audio_path: Path
    thumbnail_path: Optional[Path]


class _SilentLogger:
    def debug(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        pass

    def error(self, msg: str) -> None:
        pass


def check_ytdlp_available() -> bool:
    try:
        import yt_dlp  # noqa: F401
        return True
    except ImportError:
        return False


def _looks_restricted(message: str) -> bool:
    lower = message.lower()
    return any(marker in lower for marker in _RESTRICTED_MARKERS)


def _meta_from_info(info: dict) -> SongMeta:
    return SongMeta(
        video_id=info["id"],
        title=info.get("title") or "未知歌曲",
        artist=info.get("artist") or info.get("uploader") or info.get("channel") or "未知歌手",
        duration=info.get("duration"),
        thumbnail_url=info.get("thumbnail"),
    )


def resolve_song(url: str) -> SongMeta:
    """僅解析網址取得中繼資料（歌名/歌手/封面/影片ID），不下載媒體內容。

    用於下載前先查詢是否已有快取結果。
    """
    if not url or not url.strip():
        raise DownloadError("請輸入有效的歌曲網址")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "logger": _SilentLogger(),
        "noplaylist": True,
        "skip_download": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        message = str(exc)
        if _looks_restricted(message):
            raise RestrictedContentError(
                "此內容受登入、付費會員或 DRM 保護，本工具依政策拒絕繞過，無法處理。"
            ) from exc
        raise DownloadError(f"無法解析歌曲網址：{message}") from exc
    except Exception as exc:  # noqa: BLE001 涵蓋網路逾時等未預期錯誤
        raise DownloadError(f"解析網址時發生未預期錯誤：{exc}") from exc

    if not isinstance(info, dict) or "id" not in info:
        raise DownloadError("無法從此網址取得歌曲資訊")
    return _meta_from_info(info)


def _make_hook(progress_callback: Optional[ProgressCallback]):
    def hook(d: dict) -> None:
        if progress_callback is None:
            return
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            fraction = (downloaded / total) if total else 0.0
            progress_callback(min(fraction, 1.0), "下載歌曲中…")
        elif status == "finished":
            progress_callback(1.0, "下載完成，轉換音訊格式中…")
    return hook


def download_song(
    url: str,
    input_dir: Path,
    progress_callback: Optional[ProgressCallback] = None,
) -> DownloadedSong:
    """下載網址中的音訊（轉為 wav）與封面圖片，回傳中繼資料與檔案路徑。"""
    if not url or not url.strip():
        raise DownloadError("請輸入有效的歌曲網址")

    input_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(input_dir / "%(id)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
        "writethumbnail": True,
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
                "此內容受登入、付費會員或 DRM 保護，本工具依政策拒絕繞過，無法處理。"
            ) from exc
        raise DownloadError(f"下載失敗：{message}") from exc
    except Exception as exc:  # noqa: BLE001
        raise DownloadError(f"下載時發生未預期錯誤：{exc}") from exc

    meta = _meta_from_info(info)
    wav_path = input_dir / f"{meta.video_id}.wav"
    if not wav_path.exists():
        candidates = sorted(input_dir.glob("*.wav"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not candidates:
            raise DownloadError("下載完成但找不到輸出的音訊檔案")
        wav_path = candidates[0]

    thumbnail_path = None
    for ext in ("jpg", "jpeg", "png", "webp"):
        candidate = input_dir / f"{meta.video_id}.{ext}"
        if candidate.exists():
            thumbnail_path = candidate
            break

    return DownloadedSong(meta=meta, audio_path=wav_path, thumbnail_path=thumbnail_path)
