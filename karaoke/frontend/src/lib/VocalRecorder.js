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
    const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "";
    this.mediaRecorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : undefined);
    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) this.chunks.push(event.data);
    };
    this.mediaRecorder.start();
  }

  pause() {
    if (this.mediaRecorder?.state === "recording") this.mediaRecorder.pause();
  }

  resume() {
    if (this.mediaRecorder?.state === "paused") this.mediaRecorder.resume();
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
