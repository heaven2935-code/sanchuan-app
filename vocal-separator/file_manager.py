"""工作暫存資料夾管理：建立、儲存上傳檔案、列出與清除。"""
from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from config import JOBS_ROOT


@dataclass
class JobPaths:
    job_id: str
    root: Path
    input_dir: Path
    stems_dir: Path
    output_dir: Path


def _ensure_jobs_root() -> Path:
    JOBS_ROOT.mkdir(parents=True, exist_ok=True)
    return JOBS_ROOT


def create_job() -> JobPaths:
    """建立一個獨立的工作暫存資料夾，回傳各子目錄路徑。"""
    _ensure_jobs_root()
    job_id = uuid.uuid4().hex[:12]
    root = JOBS_ROOT / job_id
    input_dir = root / "input"
    stems_dir = root / "stems"
    output_dir = root / "output"
    for d in (input_dir, stems_dir, output_dir):
        d.mkdir(parents=True, exist_ok=True)
    return JobPaths(job_id=job_id, root=root, input_dir=input_dir, stems_dir=stems_dir, output_dir=output_dir)


def save_uploaded_file(job: JobPaths, filename: str, data: bytes) -> Path:
    """將使用者上傳的檔案寫入工作暫存資料夾，回傳檔案路徑。"""
    safe_name = Path(filename).name or "upload"
    dest = job.input_dir / safe_name
    dest.write_bytes(data)
    return dest


def list_jobs() -> list[dict]:
    """列出目前所有暫存工作，附上大小與建立時間。"""
    _ensure_jobs_root()
    jobs = []
    for d in sorted(JOBS_ROOT.iterdir()):
        if not d.is_dir():
            continue
        size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
        jobs.append({
            "job_id": d.name,
            "path": d,
            "size_bytes": size,
            "created_at": d.stat().st_mtime,
        })
    return jobs


def cleanup_job(job_id: str) -> bool:
    """刪除單一工作的暫存資料夾。"""
    target = JOBS_ROOT / job_id
    if target.exists() and target.is_dir() and target.parent == JOBS_ROOT:
        shutil.rmtree(target, ignore_errors=True)
        return True
    return False


def cleanup_all() -> int:
    """刪除所有工作暫存資料夾，回傳刪除數量。"""
    count = 0
    for job in list_jobs():
        if cleanup_job(job["job_id"]):
            count += 1
    return count


def human_readable_size(num_bytes: float) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
