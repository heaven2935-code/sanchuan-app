import { useState } from "react";

const BAR_HEIGHTS = [
  8, 14, 10, 20, 14, 28, 20, 38, 26, 48, 34, 60, 42, 74, 52, 88, 62, 98, 72, 100, 82, 100, 90, 100,
  82, 100, 72, 100, 62, 98, 52, 88, 42, 74, 34, 60, 26, 48, 20, 38, 14, 28, 10, 20, 8, 14,
];

function Waveform() {
  return (
    <div className="waveform" aria-hidden="true">
      {BAR_HEIGHTS.map((h, i) => (
        <span key={i} className="waveform__bar" style={{ height: `${h}%` }} />
      ))}
    </div>
  );
}

function LinkIcon() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M9 15 15 9" />
      <path d="M13.5 5.5 15 4a4 4 0 0 1 5.66 5.66l-1.5 1.5" />
      <path d="M10.5 18.5 9 20a4 4 0 0 1-5.66-5.66l1.5-1.5" />
    </svg>
  );
}

function ClipboardIcon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="6" y="4" width="12" height="17" rx="2" />
      <path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1" />
      <path d="M9 12h6M9 16h6" />
    </svg>
  );
}

function EqualizerIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <path d="M5 10v4" />
      <path d="M10 6v12" />
      <path d="M14 9v6" />
      <path d="M19 4v16" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3 5 6v5c0 4.5 3 7.7 7 9 4-1.3 7-4.5 7-9V6l-7-3Z" />
    </svg>
  );
}

export default function UrlForm({ onSubmit, disabled }) {
  const [url, setUrl] = useState("");
  const [pasteError, setPasteError] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  }

  async function handlePaste() {
    setPasteError(false);
    try {
      const text = await navigator.clipboard.readText();
      if (text) setUrl(text.trim());
    } catch {
      setPasteError(true);
    }
  }

  return (
    <div className="home">
      <div className="hero">
        <div className="hero__rings" aria-hidden="true">
          <span className="hero__ring hero__ring--1" />
          <span className="hero__ring hero__ring--2" />
          <span className="hero__ring hero__ring--3" />
        </div>
        <Waveform />
        <h1 className="brand-logo">
          HO<span className="brand-logo__o">O</span>KED
        </h1>
        <p className="brand-logo__sub">MUSIC</p>
        <p className="tagline">HEAR YOURSELF AT YOUR BEST.</p>
      </div>

      <form className="input-card" onSubmit={handleSubmit}>
        <div className="input-card__header">
          <span className="input-card__icon">
            <LinkIcon />
          </span>
          <div>
            <h2 className="input-card__title">貼上歌曲網址</h2>
            <p className="input-card__subtitle">支援 YouTube 等音樂來源</p>
          </div>
        </div>

        <div className="input-row">
          <input
            className="url-input"
            type="url"
            inputMode="url"
            placeholder="貼上 YouTube 或支援的歌曲網址…"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={disabled}
            aria-label="歌曲網址"
          />
          <button type="button" className="paste-button" onClick={handlePaste} disabled={disabled}>
            <ClipboardIcon /> 貼上
          </button>
        </div>
        {pasteError && <p className="paste-error">無法讀取剪貼簿，請手動貼上網址</p>}

        <button className="load-button" type="submit" disabled={disabled || !url.trim()}>
          <EqualizerIcon /> 載入歌曲
        </button>
      </form>

      <p className="disclaimer">
        <ShieldIcon /> 請確認你有權使用該音樂內容
      </p>
    </div>
  );
}
