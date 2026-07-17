// 依優先順序挑選瀏覽器支援的錄音格式：iOS Safari 不支援 audio/webm，
// 只支援 audio/mp4；桌面 Chrome/Firefox 則普遍支援 audio/webm。
const MIME_CANDIDATES = ["audio/mp4", "audio/webm", "audio/ogg"];
const EXT_BY_MIME = { "audio/mp4": "m4a", "audio/webm": "webm", "audio/ogg": "ogg" };

function pickSupportedMimeType() {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) return "";
  return MIME_CANDIDATES.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

/** 包裝 MediaRecorder：錄下麥克風輸入，供錄音回放與下載使用。 */
export class VocalRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.stream = null;
    this.chunks = [];
    this.blob = null;
  }

  async start() {
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.chunks = [];
    this.blob = null;
    const mimeType = pickSupportedMimeType();
    this.mediaRecorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : undefined);
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) this.chunks.push(event.data);
    };
    this.mediaRecorder.start();
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
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
  }
}
