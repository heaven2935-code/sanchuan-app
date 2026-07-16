# 樂癮 Karaoke — V1 MVP

手機優先的 K 歌網站。貼上歌曲網址 → 自動人聲分離 → KTV 風格播放器（原唱／伴奏／導唱／升降 Key）→
錄音、回放、下載。

## 架構

```
karaoke/
├── backend/     FastAPI：下載/人聲分離/混音、非同步 job、依影片ID快取
└── frontend/    Vite + React：貼網址、進度顯示、Web Audio API KTV 播放器、錄音
```

- **downloader.py**：yt-dlp 解析網址與下載音訊、擷取歌名/歌手/封面。拒絕繞過 DRM/付費牆/登入限制的內容。
- **separator.py**：呼叫 Demucs 分離 vocals/drums/bass/other。獨立介面，之後可替換為其他分離引擎
  （見下方「未來擴充」）。
- **mixer.py**：FFmpeg 產生 `original`（原唱）/ `instrumental`（伴奏）/ `vocals`（人聲）三軌 MP3。
- **jobs.py**：背景執行緒處理下載→分離→混音，依影片 ID 快取（同一首歌第二次請求直接秒開）。
- **main.py**：FastAPI 路由（建立/查詢工作、音軌與封面靜態檔案）。
- 前端 `KaraokeEngine.js`：用 Tone.js 同步載入三軌並用 `Tone.Transport` 統一時間軸，切換
  原唱/伴奏/導唱只是調整各軌音量（不重新載入），`Tone.PitchShift` 做即時升降 Key。
- 前端 `VocalRecorder.js`：用瀏覽器原生 `MediaRecorder` 錄下麥克風輸入，錄音全程留在瀏覽器端，
  不上傳到伺服器；回放、下載皆為本機處理。

## 開發環境需求

- Python 3.11+、Node.js 20+
- FFmpeg（需在系統 PATH）
- 首次分離歌曲需要網路連線下載 Demucs 模型權重（快取在本機，之後可離線使用）

## 啟動方式（開發環境）

後端：

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

前端：

```bash
cd frontend
npm install
npm run dev
```

瀏覽器開啟 `http://localhost:5173`。若後端跑在不同網址，於 `frontend/.env` 設定
`VITE_API_BASE=http://your-backend:8001`。

> **注意**：麥克風錄音（`getUserMedia`）需要安全情境（HTTPS 或 `localhost`）。正式上線後前端網域
> 必須是 HTTPS，否則瀏覽器會拒絕麥克風權限。

## 已知限制

- Demucs 在 CPU 上分離一首歌需要數分鐘，這是目前最大的體驗瓶頸。MVP 策略是坦然接受這個等待
  （清楚的進度顯示），並用「依影片 ID 快取」讓同一首歌之後的請求秒開，而非在 V1 就解決運算速度問題。
- 僅支援下載一般公開內容；偵測到需要登入、付費會員或 DRM 保護時會直接拒絕處理。
- 錄音與回放僅在瀏覽器本機進行，重新整理頁面後錄音內容不會保留，請於「回顧」畫面下載保存。

## 未來擴充：更換人聲分離引擎

`separator.py` 對外只暴露 `separate(audio_path, stems_dir, ...) -> {vocals, drums, bass, other}`
這個介面，`jobs.py` 只依賴這個函式簽名，不關心背後怎麼實作。之後若要：

- 換更快的模型或改用 GPU 推論
- 改接商業 API（例如 LALAL.AI、Moises）
- 依付費等級切換不同引擎

都只需要替換 `separate()` 內部實作，不需要更動 API 層、job 狀態機制、快取邏輯或前端。
