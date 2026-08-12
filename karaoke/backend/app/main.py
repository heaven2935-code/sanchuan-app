"""樂癮 KTV 後端 API。"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import downloader, jobs, mixer, separator
from .config import CORS_ORIGINS

app = FastAPI(title="樂癮 Karaoke API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateJobRequest(BaseModel):
    url: str


@app.get("/api/health")
def health() -> dict:
    return {
        "ffmpeg": mixer.check_ffmpeg_available(),
        "yt_dlp": downloader.check_ytdlp_available(),
        "demucs": separator.check_demucs_available(),
    }


@app.post("/api/jobs")
def create_job(payload: CreateJobRequest) -> dict:
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="請輸入歌曲網址")
    job = jobs.create_job(payload.url.strip())
    return {"job_id": job.job_id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="找不到此工作")
    with job.lock:
        return job.to_public_dict()


@app.get("/api/songs/{video_id}/audio/{track}")
def get_track(video_id: str, track: str):
    if track not in jobs.TRACK_NAMES:
        raise HTTPException(status_code=400, detail="不支援的音軌")
    path = jobs.tracks_dir_for(video_id) / f"{track}.mp3"
    if not path.exists():
        raise HTTPException(status_code=404, detail="找不到音軌檔案")
    return FileResponse(path, media_type="audio/mpeg")


@app.get("/api/songs/{video_id}/thumbnail")
def get_thumbnail(video_id: str):
    path = jobs.thumbnail_path_for(video_id)
    if path is None:
        raise HTTPException(status_code=404, detail="沒有封面圖片")
    return FileResponse(path)
