import * as Tone from "tone";

// 依優先順序挑選瀏覽器支援的錄音格式：iOS Safari 不支援 audio/webm，
// 只支援 audio/mp4；桌面 Chrome/Firefox 則普遍支援 audio/webm。
const MIME_CANDIDATES = ["audio/mp4", "audio/webm", "audio/ogg"];
const EXT_BY_MIME = { "audio/mp4": "m4a", "audio/webm": "webm", "audio/ogg": "ogg" };

function pickSupportedMimeType() {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return "";
  return MIME_CANDIDATES.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

/**
 * 包裝 MediaRecorder：錄下麥克風聲音，若有提供伴奏／導唱的 backingStream，
 * 會在同一個 AudioContext 內把麥克風與伴奏混音成同一軌再錄製，讓錄音聽起來
 * 像一次完整的 KTV 演唱（人聲 + 伴奏），而不是只有乾淨的人聲。
 */
export class VocalRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.micStream = null;
    this.micGain = null;
    this.mixNodes = [];
    this.chunks = [];
    this.blob = null;
  }

  async start(backingStream, micVolume = 1) {
    this.micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.blob = null;
    this.mixNodes = [];

    // 一律經過同一個 AudioContext 混音，麥克風先過一個可調音量的 Gain 節點，
    // 才能讓「麥克風音量」滑桿即時生效（包含錄音中途調整）。
    const ctx = Tone.getContext().rawContext;
    const dest = ctx.createMediaStreamDestination();
    const micSource = ctx.createMediaStreamSource(this.micStream);
    const micGain = ctx.createGain();
    micGain.gain.value = micVolume;
    micSource.connect(micGain).connect(dest);
    this.micGain = micGain;
    this.mixNodes = [micSource, micGain, dest];

    if (backingStream) {
      const backingSource = ctx.createMediaStreamSource(backingStream);
      backingSource.connect(dest);
      this.mixNodes.push(backingSource);
    }

    const mimeType = pickSupportedMimeType();
    this.mediaRecorder = new MediaRecorder(dest.stream, mimeType ? { mimeType } : undefined);
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) this.chunks.push(event.data);
    };
    this.mediaRecorder.start();
  }

  /** 調整錄音中麥克風音量（0～可超過1做增益放大），錄音中途也能即時生效。 */
  setMicVolume(value) {
    if (this.micGain) this.micGain.gain.value = value;
  }

  pause() {
    try {
      if (this.mediaRecorder?.state === "recording") this.mediaRecorder.pause();
    } catch (err) {
      console.error("MediaRecorder.pause 不支援或失敗", err);
    }
  }

  resume() {
    try {
      if (this.mediaRecorder?.state === "paused") this.mediaRecorder.resume();
    } catch (err) {
      console.error("MediaRecorder.resume 不支援或失敗", err);
    }
  }

  /** 回傳目前錄音檔案建議的副檔名（依實際使用的 mimeType 判斷）。 */
  getFileExtension() {
    const mimeType = this.blob?.type || this.mediaRecorder?.mimeType || "";
    const base = mimeType.split(";")[0].trim();
    return EXT_BY_MIME[base] || "webm";
  }

  stop() {
    return new Promise((resolve) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
        resolve(this.blob);
        return;
      }
      this.mediaRecorder.onstop = () => {
        this.blob = new Blob(this.chunks, { type: this.mediaRecorder.mimeType || "audio/webm" });
        this._releaseStream();
        resolve(this.blob);
      };
      this.mediaRecorder.stop();
    });
  }

  cancel() {
    if (this.mediaRecorder?.state !== "inactive") this.mediaRecorder?.stop();
    this._releaseStream();
    this.chunks = [];
    this.blob = null;
  }

  _releaseStream() {
    // 只停止麥克風的 track；backingStream 的 track 屬於 KaraokeEngine，
    // 由它自己管理生命週期，這裡不能停用，否則會中斷播放器的錄音輸出。
    this.micStream?.getTracks().forEach((track) => track.stop());
    this.micStream = null;
    this.micGain = null;
    this.mixNodes.forEach((node) => node.disconnect());
    this.mixNodes = [];
  }
}
