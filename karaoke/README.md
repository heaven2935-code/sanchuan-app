# HOOKED MUSIC — V1 MVP

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

## Demo／Fixture 模式（手機測試用）

`frontend` 內建一個完全不需要後端的 Demo 模式，方便在沒有後端可連線（例如純靜態網頁託管）
的情況下，於手機上測試完整互動流程：貼網址（實際上不會真的連線）→ 模擬處理進度 → KTV
播放器（合成測試音效）→ 原唱/伴奏/導唱切換 → 升降 Key → 播放同時錄音 → 回顧回放 → 下載/
重新演唱。

- 開啟方式：建置時設定環境變數 `VITE_DEMO_MODE=true`（`npm run build:demo` 已內建此設定）。
- 畫面最上方會持續顯示醒目的黃色「示範模式 Demo」橫幅，歌曲標題也會標註「非真實分離結果」，
  確保使用者不會誤以為是真的處理了他們貼的網址。
- Demo 音檔（`frontend/public/demo/*.mp3`）為合成測試音效，非真實歌曲、非真實人聲分離結果。
- 實作於 `src/lib/demoApi.js`，與真後端 `src/lib/api.js` 實作同一組介面
  （`createJob/getJob/trackUrl/thumbnailUrl`），由 `src/lib/apiProvider.js` 依
  `VITE_DEMO_MODE` 切換，其餘元件一律從 `apiProvider` import，不需要另外改動。

## 部署（目前已上線的狀態）

### 後端：Render

真實後端已部署在 Render，服務網址：`https://karaoke-backend-mchf.onrender.com`
（repo 根目錄的 `render.yaml` 是對應的 Blueprint 設定檔，`CORS_ORIGINS` 已設為
GitHub Pages 前端的網域）。

`backend/Dockerfile` 支援以下環境變數：

| 環境變數 | 說明 | 目前設定 |
|---|---|---|
| `PORT` | 監聽埠（平台自動注入） | Render 自動指定 |
| `CORS_ORIGINS` | 允許呼叫 API 的前端網域，逗號分隔 | `https://heaven2935-code.github.io` |
| `CACHE_DIR` | 快取／工作資料目錄 | 容器內 `/app/data/cache` |

> ⚠️ Demucs + PyTorch 需要一定的記憶體，方案規格太小（例如最低階 512MB）處理歌曲時可能
> OOM 當機，建議選擇記憶體至少 2GB 的方案；若處理常常失敗，先確認目前方案的記憶體大小。

### 前端：GitHub Pages（已設定自動部署，接正式後端）

`.github/workflows/deploy-karaoke-demo.yml` 會在推送到本分支時自動建置前端並部署到
GitHub Pages：`https://heaven2935-code.github.io/sanchuan-app/karaoke/`，建置時已指定
`VITE_API_BASE` 指向上面的 Render 後端網址，**不是 Demo 模式**，會真的呼叫後端下載/分離歌曲。

若要切回 Demo／Fixture 模式（例如後端維護中暫時想展示 UI），把該 workflow 的建置步驟改回
`npm run build:demo` 即可，不需要改動任何原始碼。

首次啟用 Pages 若 repo 從未設定過，可能需要到 repo 的 **Settings → Pages → Build and
deployment → Source** 手動選擇一次「GitHub Actions」（僅需一次）。

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
