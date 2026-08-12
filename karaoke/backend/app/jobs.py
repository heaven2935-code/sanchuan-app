"""工作(job)狀態管理：背景執行下載/分離/混音，並依影片 ID 快取結果。"""
from __future__ import annotations

import json
import shutil
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import downloader, mixer, separator
from .config import CACHE_ROOT

TRACK_NAMES = ("original", "instrumental", "vocals")


@dataclass
class JobState:
    job_id: str
    status: str = "pending"  # pending|resolving|downloading|separating|mixing|ready|error
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    video_id: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None
    duration: Optional[float] = None
    has_thumbnail: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def to_public_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "video_id": self.video_id,
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "has_thumbnail": self.has_thumbnail,
        }


_jobs: dict[str, JobState] = {}
_jobs_lock = threading.Lock()


def get_job(job_id: str) -> Optional[JobState]:
    with _jobs_lock:
        return _jobs.get(job_id)


def cache_dir_for(video_id: str) -> Path:
    return CACHE_ROOT / video_id


def tracks_dir_for(video_id: str) -> Path:
    return cache_dir_for(video_id) / "tracks"


def thumbnail_path_for(video_id: str) -> Optional[Path]:
    cache_dir = cache_dir_for(video_id)
    meta = _read_meta(cache_dir)
    if not meta or not meta.get("thumbnail_ext"):
        return None
    path = cache_dir / f"thumbnail.{meta['thumbnail_ext']}"
    return path if path.exists() else None


def _meta_path(cache_dir: Path) -> Path:
    return cache_dir / "meta.json"


def _read_meta(cache_dir: Path) -> Optional[dict]:
    path = _meta_path(cache_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _write_meta(cache_dir: Path, title: str, artist: str, duration: float, thumbnail_ext: Optional[str]) -> None:
    data = {"title": title, "artist": artist, "duration": duration, "thumbnail_ext": thumbnail_ext}
    _meta_path(cache_dir).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _is_cache_ready(cache_dir: Path) -> bool:
    meta = _read_meta(cache_dir)
    if meta is None:
        return False
    tracks_dir = cache_dir / "tracks"
    return all((tracks_dir / f"{name}.mp3").exists() for name in TRACK_NAMES)


def create_job(url: str) -> JobState:
    job_id = uuid.uuid4().hex[:12]
    job = JobState(job_id=job_id, status="pending", message="準備中…")
    with _jobs_lock:
        _jobs[job_id] = job
    thread = threading.Thread(target=_process_job, args=(job, url), daemon=True)
    thread.start()
    return job


def _update(job: JobState, **kwargs) -> None:
    with job.lock:
        for key, value in kwargs.items():
            setattr(job, key, value)


def _process_job(job: JobState, url: str) -> None:
    try:
        _update(job, status="resolving", progress=0.0, message="解析歌曲網址中…")
        meta = downloader.resolve_song(url)
        cache_dir = cache_dir_for(meta.video_id)
        tracks_dir = cache_dir / "tracks"
        _update(job, video_id=meta.video_id, title=meta.title, artist=meta.artist, duration=meta.duration)

        cached_meta = _read_meta(cache_dir)
        if cached_meta and _is_cache_ready(cache_dir):
            _update(
                job, status="ready", progress=1.0, message="已從快取讀取，可直接播放",
                title=cached_meta["title"], artist=cached_meta["artist"], duration=cached_meta["duration"],
                has_thumbnail=cached_meta.get("thumbnail_ext") is not None,
            )
            return

        input_dir = cache_dir / "input"
        stems_dir = cache_dir / "stems"
        for stale in (input_dir, stems_dir, tracks_dir):
            shutil.rmtree(stale, ignore_errors=True)

        def download_progress(fraction: float, message: str) -> None:
            _update(job, status="downloading", progress=0.05 + fraction * 0.25, message=message)

        _update(job, status="downloading", progress=0.05, message="下載歌曲中…")
        song = downloader.download_song(url, input_dir, progress_callback=download_progress)
        _update(job, title=song.meta.title, artist=song.meta.artist, duration=song.meta.duration)

        def separate_progress(fraction: float, message: str) -> None:
            _update(job, status="separating", progress=0.3 + fraction * 0.55, message=message)

        stems = separator.separate(song.audio_path, stems_dir, progress_callback=separate_progress)

        def mix_progress(fraction: float, message: str) -> None:
            _update(job, status="mixing", progress=0.85 + fraction * 0.15, message=message)

        tracks = mixer.render_tracks(song.audio_path, stems, tracks_dir, progress_callback=mix_progress)

        thumbnail_ext = None
        if song.thumbnail_path is not None:
            thumbnail_ext = song.thumbnail_path.suffix.lstrip(".")
            shutil.copy(song.thumbnail_path, cache_dir / f"thumbnail.{thumbnail_ext}")

        duration = song.meta.duration or mixer.probe_duration(tracks["original"])
        _write_meta(cache_dir, song.meta.title, song.meta.artist, duration, thumbnail_ext)

        shutil.rmtree(input_dir, ignore_errors=True)
        shutil.rmtree(stems_dir, ignore_errors=True)

        _update(
            job, status="ready", progress=1.0, message="處理完成",
            duration=duration, has_thumbnail=thumbnail_ext is not None,
        )
    except downloader.RestrictedContentError as exc:
        _update(job, status="error", error=str(exc), message="已拒絕處理")
    except (downloader.DownloadError, separator.SeparationError, mixer.MixError) as exc:
        _update(job, status="error", error=str(exc), message="處理失敗")
    except Exception as exc:  # noqa: BLE001 保底錯誤處理，避免背景執行緒靜默中止
        _update(job, status="error", error=f"發生未預期錯誤：{exc}", message="處理失敗")
