import { useEffect, useRef, useState } from "react";
import { KaraokeEngine } from "../lib/KaraokeEngine";
import { VocalRecorder } from "../lib/VocalRecorder";
import { trackUrl, thumbnailUrl } from "../lib/apiProvider";
import { formatTime } from "../lib/format";

const MODES = [
  { key: "original", label: "原唱" },
  { key: "instrumental", label: "伴奏" },
  { key: "guide", label: "導唱" },
];

export default function KaraokePlayer({ job, onReset }) {
  const engineRef = useRef(null);
  const recorderRef = useRef(null);
  const reviewAudioRef = useRef(null);
  const rafRef = useRef(null);

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [mode, setMode] = useState("guide");
  const [semitones, setSemitones] = useState(0);
  const [playbackVolume, setPlaybackVolume] = useState(100);
  const [micVolume, setMicVolume] = useState(100);
  const [position, setPosition] = useState(0);
  const [duration, setDuration] = useState(job.duration || 0);
  const [playState, setPlayState] = useState("ready"); // ready | singing | paused | reviewing
  const [recordingUrl, setRecordingUrl] = useState(null);
  const [recordingExt, setRecordingExt] = useState("webm");
  const [reviewPosition, setReviewPosition] = useState(0);
  const [reviewDuration, setReviewDuration] = useState(0);
  const [reviewPlaying, setReviewPlaying] = useState(false);
  const [thumbOk, setThumbOk] = useState(job.has_thumbnail);

  useEffect(() => {
    let cancelled = false;
    const engine = new KaraokeEngine();
    engineRef.current = engine;
    recorderRef.current = new VocalRecorder();

    engine
      .load({
        original: trackUrl(job.video_id, "original"),
        instrumental: trackUrl(job.video_id, "instrumental"),
        vocals: trackUrl(job.video_id, "vocals"),
      })
      .then(() => {
        if (cancelled) return;
        setDuration(engine.duration || job.duration || 0);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        console.error(err);
        setLoadError("歌曲載入失敗，請重新嘗試。");
        setLoading(false);
      });

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafRef.current);
      engine.dispose();
      recorderRef.current?.cancel();
      if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job.video_id]);

  useEffect(() => {
    if (playState !== "singing") return undefined;
    const tick = () => {
      const engine = engineRef.current;
      if (!engine) return;
      const pos = engine.position;
      setPosition(pos);
      if (duration > 0 && pos >= duration - 0.05) {
        handleFinishSinging();
        return;
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playState, duration]);

  async function handlePlayPause() {
    const engine = engineRef.current;
    const recorder = recorderRef.current;
    if (!engine) return;

    if (playState === "ready") {
      // iOS Safari 等瀏覽器要求 AudioContext resume 必須緊跟在使用者手勢後，
      // 中間不能先 await 其他非音訊的非同步操作（例如麥克風權限請求），
      // 否則會被視為不是使用者手勢觸發而靜音。所以先啟動音訊，再要求錄音權限。
      await engine.play();
      try {
        await recorder.start(engine.getBackingStream(), micVolume / 100);
      } catch (err) {
        console.error(err);
        alert("無法取得麥克風權限，將僅播放歌曲不錄音。");
      }
      setPlayState("singing");
    } else if (playState === "singing") {
      engine.pause();
      recorder.pause();
      setPlayState("paused");
    } else if (playState === "paused") {
      await engine.play();
      recorder.resume();
      setPlayState("singing");
    }
  }

  async function handleFinishSinging() {
    const engine = engineRef.current;
    const recorder = recorderRef.current;
    engine.pause();
    cancelAnimationFrame(rafRef.current);
    const blob = await recorder.stop();
    if (blob && blob.size > 0) {
      setRecordingUrl(URL.createObjectURL(blob));
      setRecordingExt(recorder.getFileExtension());
    }
    setPlayState("reviewing");
  }

  function handleRestart() {
    engineRef.current.seek(0);
    setPosition(0);
    if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    setRecordingUrl(null);
    setRecordingExt("webm");
    setPlayState("ready");
  }

  function handleSeek(e) {
    const value = Number(e.target.value);
    engineRef.current.seek(value);
    setPosition(value);
  }

  function handleModeChange(nextMode) {
    setMode(nextMode);
    engineRef.current?.applyMode(nextMode);
  }

  function handleSemitoneChange(delta) {
    const next = Math.max(-6, Math.min(6, semitones + delta));
    setSemitones(next);
    engineRef.current?.setSemitones(next);
  }

  function handlePlaybackVolumeChange(e) {
    const value = Number(e.target.value);
    setPlaybackVolume(value);
    engineRef.current?.setPlaybackVolume(value / 100);
  }

  function handleMicVolumeChange(e) {
    const value = Number(e.target.value);
    setMicVolume(value);
    recorderRef.current?.setMicVolume(value / 100);
  }

  function toggleReviewPlay() {
    const audio = reviewAudioRef.current;
    if (!audio) return;
    if (reviewPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
  }

  if (loading) {
    return <div className="progress-panel">🎵 歌曲載入中…</div>;
  }

  if (loadError) {
    return (
      <div className="progress-panel progress-panel--error">
        <p className="progress-message">❌ {loadError}</p>
        <button className="secondary-button" onClick={onReset}>
          重新輸入網址
        </button>
      </div>
    );
  }

  return (
    <div className="karaoke-player">
      <div className="cover-area">
        {thumbOk ? (
          <img
            className="cover-image"
            src={thumbnailUrl(job.video_id)}
            alt={job.title}
            onError={() => setThumbOk(false)}
          />
        ) : (
          <div className="cover-placeholder">🎵</div>
        )}
      </div>
      <h2 className="song-title">{job.title}</h2>
      <p className="song-artist">{job.artist}</p>

      {playState !== "reviewing" ? (
        <>
          <div className="timeline">
            <span className="time-label">{formatTime(position)}</span>
            <input
              className="seek-slider"
              type="range"
              min={0}
              max={duration || 0}
              step={0.1}
              value={Math.min(position, duration || 0)}
              onChange={handleSeek}
              disabled={playState !== "ready"}
            />
            <span className="time-label">{formatTime(duration)}</span>
          </div>

          <div className="mode-switch">
            {MODES.map((m) => (
              <button
                key={m.key}
                className={`mode-button ${mode === m.key ? "mode-button--active" : ""}`}
                onClick={() => handleModeChange(m.key)}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div className="key-control">
            <span>升降 Key</span>
            <button className="key-button" onClick={() => handleSemitoneChange(-1)} aria-label="降 Key">
              −
            </button>
            <span className="key-value">{semitones > 0 ? `+${semitones}` : semitones}</span>
            <button className="key-button" onClick={() => handleSemitoneChange(1)} aria-label="升 Key">
              +
            </button>
          </div>

          <div className="volume-controls">
            <div className="volume-row">
              <span className="volume-icon" aria-hidden="true">🔊</span>
              <input
                className="volume-slider"
                type="range"
                min={0}
                max={100}
                value={playbackVolume}
                onChange={handlePlaybackVolumeChange}
                aria-label="播放音量"
              />
              <span className="volume-value">{playbackVolume}%</span>
            </div>
            <div className="volume-row">
              <span className="volume-icon" aria-hidden="true">🎙️</span>
              <input
                className="volume-slider"
                type="range"
                min={0}
                max={150}
                value={micVolume}
                onChange={handleMicVolumeChange}
                aria-label="麥克風音量"
              />
              <span className="volume-value">{micVolume}%</span>
            </div>
          </div>

          <div className="transport-controls">
            <button className="play-button" onClick={handlePlayPause}>
              {playState === "singing" ? "⏸ 暫停" : "▶ 播放"}
            </button>
            {(playState === "singing" || playState === "paused") && (
              <button className="secondary-button" onClick={handleFinishSinging}>
                結束並回顧錄音
              </button>
            )}
          </div>
        </>
      ) : (
        <div className="review-panel">
          <p className="review-title">🎧 回顧你的演唱</p>
          {recordingUrl ? (
            <>
              <audio
                ref={reviewAudioRef}
                src={recordingUrl}
                onLoadedMetadata={(e) => setReviewDuration(e.target.duration || 0)}
                onTimeUpdate={(e) => setReviewPosition(e.target.currentTime)}
                onPlay={() => setReviewPlaying(true)}
                onPause={() => setReviewPlaying(false)}
                onEnded={() => setReviewPlaying(false)}
              />
              <div className="timeline">
                <span className="time-label">{formatTime(reviewPosition)}</span>
                <input
                  className="seek-slider"
                  type="range"
                  min={0}
                  max={reviewDuration || 0}
                  step={0.1}
                  value={Math.min(reviewPosition, reviewDuration || 0)}
                  onChange={(e) => {
                    const value = Number(e.target.value);
                    if (reviewAudioRef.current) reviewAudioRef.current.currentTime = value;
                    setReviewPosition(value);
                  }}
                />
                <span className="time-label">{formatTime(reviewDuration)}</span>
              </div>
              <div className="transport-controls">
                <button className="play-button" onClick={toggleReviewPlay}>
                  {reviewPlaying ? "⏸ 暫停" : "▶ 播放錄音"}
                </button>
              </div>
              <div className="review-actions">
                <button className="secondary-button" onClick={handleRestart}>
                  重新演唱
                </button>
                <a
                  className="download-button"
                  href={recordingUrl}
                  download={`HOOKED-錄音-${job.title || "song"}.${recordingExt}`}
                >
                  下載錄音
                </a>
              </div>
            </>
          ) : (
            <>
              <p className="progress-message">沒有取得麥克風錄音（可能未授權麥克風權限）。</p>
              <button className="secondary-button" onClick={handleRestart}>
                重新演唱
              </button>
            </>
          )}
        </div>
      )}

      <button className="link-button" onClick={onReset}>
        ⟲ 換一首歌
      </button>
    </div>
  );
}
