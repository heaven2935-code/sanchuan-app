import { useState } from "react";

const BAR_HEIGHTS = [
  14, 22, 10, 30, 18, 40, 24, 55, 32, 70, 45, 85, 60, 95, 70, 100, 78, 100, 70, 95, 60, 85, 45, 70,
  32, 55, 24, 40, 18, 30, 10, 22, 14,
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
        <p className="tagline">HEAR YOURSELF AT YOUR BEST</p>
      </div>

      <form className="input-card" onSubmit={handleSubmit}>
        <div className="input-card__header">
          <span className="input-card__icon">🔗</span>
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
            📋 貼上
          </button>
        </div>
        {pasteError && <p className="paste-error">無法讀取剪貼簿，請手動貼上網址</p>}

        <button className="load-button" type="submit" disabled={disabled || !url.trim()}>
          🎵 載入歌曲
        </button>
      </form>

      <p className="disclaimer">🛡️ 請確認你有權使用該音樂內容</p>
    </div>
  );
}
