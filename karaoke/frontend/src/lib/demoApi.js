/**
 * Demo／Fixture 模式：完全在瀏覽器端模擬處理流程，不呼叫任何後端，
 * 也不會真的下載或分離使用者貼上的網址。用於展示 UI／播放器／錄音
 * 功能，讓沒有後端可連線時也能在手機上完整試用互動流程。
 *
 * 音檔為合成測試音效（非真實歌曲、非真實人聲分離結果）。
 */

export const DEMO_AUDIO_DURATION = 20;
export const DEMO_TITLE = "示範歌曲（Demo 測試音效，非真實分離結果）";
export const DEMO_ARTIST = "樂癮 Demo";

const TOTAL_MS = 3200;
const STAGES = [
  { status: "resolving", message: "解析歌曲網址中…（Demo 模式，未連線真實網路）", from: 0, to: 0.15 },
  { status: "downloading", message: "模擬下載歌曲中…（Demo 模式）", from: 0.15, to: 0.45 },
  { status: "separating", message: "模擬人聲分離中…（Demo 測試音效，非真實分離）", from: 0.45, to: 0.85 },
  { status: "mixing", message: "模擬混音中…（Demo 模式）", from: 0.85, to: 1 },
];

const jobStartedAt = new Map();

function randomId() {
  return Math.random().toString(36).slice(2, 10);
}

export async function createJob(_url) {
  const jobId = `demo-${Date.now()}-${randomId()}`;
  jobStartedAt.set(jobId, Date.now());
  return { job_id: jobId };
}

export async function getJob(jobId) {
  const startedAt = jobStartedAt.get(jobId);
  if (!startedAt) {
    throw new Error("找不到此工作（Demo 模式）");
  }
  const elapsed = Date.now() - startedAt;
  const fraction = Math.min(elapsed / TOTAL_MS, 1);

  if (fraction >= 1) {
    return {
      job_id: jobId,
      status: "ready",
      progress: 1,
      message: "Demo 模擬處理完成（測試音效，非真實分離結果）",
      error: null,
      video_id: "demo-fixture",
      title: DEMO_TITLE,
      artist: DEMO_ARTIST,
      duration: DEMO_AUDIO_DURATION,
      has_thumbnail: true,
    };
  }

  const stage = STAGES.find((s) => fraction >= s.from && fraction < s.to) || STAGES[0];
  return {
    job_id: jobId,
    status: stage.status,
    progress: fraction,
    message: stage.message,
    error: null,
    video_id: null,
    title: null,
    artist: null,
    duration: null,
    has_thumbnail: false,
  };
}

export function trackUrl(_videoId, track) {
  return `${import.meta.env.BASE_URL}demo/${track}.mp3`;
}

export function thumbnailUrl(_videoId) {
  return `${import.meta.env.BASE_URL}demo/cover.png`;
}
