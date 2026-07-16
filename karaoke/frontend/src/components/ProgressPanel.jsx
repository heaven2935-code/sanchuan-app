const STATUS_LABELS = {
  pending: "準備中…",
  resolving: "解析歌曲網址中…",
  downloading: "下載歌曲中…",
  separating: "人聲分離中（首次處理可能需要幾分鐘，請耐心等候）…",
  mixing: "混音中…",
};

export default function ProgressPanel({ job, onRetry, onCancel }) {
  if (job?.status === "error") {
    return (
      <div className="progress-panel progress-panel--error">
        <p className="progress-message">❌ {job.error || "處理失敗"}</p>
        <button className="secondary-button" onClick={onRetry}>
          重新輸入網址
        </button>
      </div>
    );
  }

  const percent = Math.round((job?.progress ?? 0) * 100);
  const label = STATUS_LABELS[job?.status] || "處理中…";

  return (
    <div className="progress-panel">
      <p className="progress-message">{label}</p>
      <div className="progress-bar">
        <div className="progress-bar__fill" style={{ width: `${percent}%` }} />
      </div>
      <p className="progress-percent">{percent}%</p>
      <button className="secondary-button" onClick={onCancel}>
        取消
      </button>
    </div>
  );
}
