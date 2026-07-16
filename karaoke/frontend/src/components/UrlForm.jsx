import { useState } from "react";

export default function UrlForm({ onSubmit, disabled }) {
  const [url, setUrl] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = url.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  }

  return (
    <form className="url-form" onSubmit={handleSubmit}>
      <h1 className="brand">🎤 樂癮</h1>
      <p className="tagline">貼上歌曲網址，馬上開始唱</p>
      <input
        className="url-input"
        type="url"
        inputMode="url"
        placeholder="貼上歌曲網址…"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        disabled={disabled}
        aria-label="歌曲網址"
      />
      <button className="load-button" type="submit" disabled={disabled || !url.trim()}>
        載入歌曲
      </button>
    </form>
  );
}
