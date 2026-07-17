import * as Tone from "tone";

const TRACKS = ["original", "instrumental", "vocals"];
const GUIDE_VOCAL_GAIN = 0.25;

/**
 * 封裝 Tone.js：同時載入原唱/伴奏/人聲三軌並保持採樣同步播放，
 * 切換模式只調整各軌音量（不重新載入/不需重新對齊），並提供共用的
 * 升降 Key（PitchShift）與 Transport 時間軸控制。
 */
export class KaraokeEngine {
  constructor() {
    this.players = {};
    this.gains = {};
    this.pitchShift = null;
    this.mode = "guide";
    this.duration = 0;
    this.loaded = false;
    this._disposed = false;
  }

  async load(urls) {
    const pitchShift = new Tone.PitchShift({ pitch: 0 }).toDestination();

    const players = {};
    const gains = {};
    await Promise.all(
      TRACKS.map(
        (name) =>
          new Promise((resolve, reject) => {
            const gain = new Tone.Gain(0).connect(pitchShift);
            const player = new Tone.Player({
              url: urls[name],
              onload: () => resolve(),
              onerror: (err) => reject(err),
            }).connect(gain);
            players[name] = player;
            gains[name] = gain;
          })
      )
    );

    if (this._disposed) {
      // 載入完成前這個引擎已被卸載（例如元件快速卸載或切換歌曲），
      // 捨棄剛建立的節點，避免殘留音訊資源。
      Object.values(players).forEach((p) => p.dispose());
      Object.values(gains).forEach((g) => g.dispose());
      pitchShift.dispose();
      return;
    }

    this.pitchShift = pitchShift;
    this.players = players;
    this.gains = gains;
    this.duration = Math.max(...TRACKS.map((name) => this.players[name].buffer.duration));
    TRACKS.forEach((name) => this.players[name].sync().start(0));
    this.applyMode(this.mode);

    // 額外把最終混音（含升降Key）接到一個 MediaStreamDestination，
    // 供錄音時跟麥克風一起混音，讓錄下來的檔案聽起來像完整的 KTV 演唱
    // （而不是只有乾淨的人聲）。
    this._recordingDestination = Tone.getContext().rawContext.createMediaStreamDestination();
    this.pitchShift.connect(this._recordingDestination);

    this.loaded = true;
  }

  /** 目前播放器輸出（伴奏/導唱/原唱，依模式與音量而定）的 MediaStream，供錄音混音使用。 */
  getBackingStream() {
    return this._recordingDestination ? this._recordingDestination.stream : null;
  }

  applyMode(mode) {
    this.mode = mode;
    if (!this.gains.original) return;
    this.gains.original.gain.value = mode === "original" ? 1 : 0;
    this.gains.instrumental.gain.value = mode === "original" ? 0 : 1;
    this.gains.vocals.gain.value = mode === "guide" ? GUIDE_VOCAL_GAIN : 0;
  }

  setSemitones(semitones) {
    this.pitchShift.pitch = semitones;
  }

  async play() {
    await Tone.start();
    if (Tone.Transport.seconds >= this.duration) {
      Tone.Transport.seconds = 0;
    }
    Tone.Transport.start();
  }

  pause() {
    Tone.Transport.pause();
  }

  seek(seconds) {
    const clamped = Math.max(0, Math.min(seconds, this.duration));
    Tone.Transport.seconds = clamped;
  }

  get position() {
    return Tone.Transport.seconds;
  }

  get isPlaying() {
    return Tone.Transport.state === "started";
  }

  dispose() {
    if (this._disposed) return;
    this._disposed = true;
    Tone.Transport.stop();
    Tone.Transport.cancel();
    TRACKS.forEach((name) => {
      this.players[name]?.dispose();
      this.gains[name]?.dispose();
    });
    this.pitchShift?.dispose();
    this.players = {};
    this.gains = {};
    this.loaded = false;
  }
}
