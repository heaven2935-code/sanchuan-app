# 音樂人聲分離工具（Windows 本機版）

使用 [Demucs](https://github.com/facebookresearch/demucs) 將音樂分離為人聲與伴奏，
一鍵產生**純伴唱版**、**導唱版**（人聲音量可調）與**純人聲版**，全部在你自己的電腦上處理，
不上傳任何檔案到外部伺服器。

## 功能

- 貼上影音網址（yt-dlp 支援的網站）或直接上傳 MP3 / WAV / M4A / MP4 檔案
- 使用 Demucs（`htdemucs` 模型）分離 vocals / drums / bass / other 四軌
- 產生三種輸出：
  - **純伴唱版**：排除人聲（drums + bass + other）
  - **導唱版**：伴奏 + 可調整音量的人聲（滑桿 0%～100%，預設 20%）
  - **純人聲版**：僅人聲
- 輸出格式：MP3 320kbps 與／或 WAV
- 處理進度與錯誤訊息即時顯示於畫面
- 每個工作使用獨立暫存資料夾，處理完成後才提供下載
- 一鍵清除暫存檔（可個別刪除或全部清除）
- 啟動時自動檢查 FFmpeg / yt-dlp / Demucs 是否安裝，缺少時顯示 Windows 安裝方式

## ⚠️ 使用規範

本工具僅供處理**你擁有合法使用權**（自行創作、已取得授權，或版權方允許）的音樂內容。
本工具**不會、也不允許**用於繞過 DRM 保護、付費牆或登入限制取得受限內容——
下載模組偵測到此類內容時會直接拒絕處理。請自行確保使用行為符合當地著作權法規。

## 技術規格

| 項目 | 技術 |
|---|---|
| 語言 | Python 3.11 |
| 介面 | Streamlit |
| 網址下載 | yt-dlp |
| 人聲分離 | Demucs（PyTorch） |
| 混音／轉檔／音量調整 | FFmpeg |

## 系統需求

- Windows 10 / 11
- [Python 3.11](https://www.python.org/downloads/)（安裝時請勾選 "Add python.exe to PATH"）
- [FFmpeg](https://www.gyan.dev/ffmpeg/builds/)（需在系統 PATH 中）
- 至少 5GB 可用磁碟空間（PyTorch + Demucs 模型）
- 建議 8GB 以上記憶體；沒有獨立顯示卡也可用 CPU 執行（速度較慢）
- 首次執行需要網路連線，用來下載 Demucs 模型權重（約數百 MB，僅下載一次並快取於本機）

## 安裝

1. 下載 / clone 本專案資料夾
2. 雙擊執行 `install.bat`
   - 會自動檢查 Python、FFmpeg
   - 建立虛擬環境 `.venv` 並安裝 `requirements.txt` 內的套件
   - 若缺少 FFmpeg 或 Python，畫面會提示安裝方式

若要手動安裝：

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 啟動

雙擊執行 `start.bat`，或手動執行：

```bat
.venv\Scripts\activate
streamlit run app.py
```

瀏覽器會自動開啟 `http://localhost:8501`。若程式偵測到缺少 FFmpeg / yt-dlp / Demucs，
畫面上方的「環境檢查」區塊會列出缺少項目與對應的 Windows 安裝方式。

## 使用方式

1. 選擇「貼上網址」或「上傳檔案」分頁，輸入影音網址或選擇本機檔案
2. 拖曳「導唱人聲音量」滑桿調整導唱版的人聲音量（0%～100%，預設 20%）
3. 勾選輸出格式（MP3 320kbps／WAV，可複選）
4. 點擊「開始處理」，等待下載／分離／混音進度完成
5. 於下方「下載結果」區塊下載純伴唱版、導唱版、純人聲版
6. 需要時可於「清除暫存檔」區塊刪除單一或全部工作暫存資料夾

## 專案結構

```
vocal-separator/
├── app.py            # Streamlit 前端與流程整合
├── downloader.py      # yt-dlp 網址下載
├── separator.py       # Demucs 人聲分離
├── mixer.py            # FFmpeg 混音／轉檔／音量調整
├── file_manager.py     # 工作暫存資料夾建立與清除
├── config.py            # 共用設定常數
├── requirements.txt
├── install.bat
├── start.bat
└── README.md
```

暫存工作資料夾位於系統暫存目錄（`%TEMP%\vocal_separator_jobs\<工作代碼>`），
每個工作互相獨立，包含 `input/`（原始音訊）、`stems/`（Demucs 分離結果）、
`output/`（最終輸出檔案）三個子資料夾。

## 疑難排解

**啟動後畫面顯示「缺少 FFmpeg」**
安裝 FFmpeg 並確認已加入系統 PATH（`winget install --id Gyan.FFmpeg -e` 或
`choco install ffmpeg`，或手動下載後將 `bin` 目錄加入 PATH），然後重新開啟命令提示字元。

**第一次處理很慢／卡在「正在載入 Demucs 模型」**
首次執行會自動下載 Demucs 模型權重（數百 MB），需要網路連線；若公司網路有防火牆
阻擋 `dl.fbaipublicfiles.com`，請改用可正常連網的環境下載一次，模型會快取在
`%USERPROFILE%\.cache\torch\hub\checkpoints\`，之後即可離線使用。

**分離速度很慢**
沒有 NVIDIA GPU 時預設使用 CPU 運算，一首 3～5 分鐘歌曲可能需要數分鐘處理時間，
屬正常現象；有 CUDA 顯示卡與對應版本的 PyTorch 可大幅加速。

**下載網址時顯示「內容受登入、付費會員或 DRM 保護」**
本工具依政策拒絕繞過此類限制，請改用你有合法使用權的來源。

## 開發模組說明

- `downloader.py`：包裝 yt-dlp，僅使用公開存取方式下載音訊並轉為 wav；偵測到需要
  登入／付費／DRM 保護的內容時拋出 `RestrictedContentError` 並拒絕下載。
- `separator.py`：以子行程呼叫 `python -m demucs` 執行人聲分離，解析輸出進度並回傳
  vocals / drums / bass / other 四軌檔案路徑。
- `mixer.py`：包裝 FFmpeg，提供音軌混音（`amix` + `volume` + `alimiter`）、格式轉換
  （MP3 320kbps／WAV）與音量調整，產生純伴唱版、導唱版、純人聲版。
- `file_manager.py`：管理每個工作的獨立暫存資料夾，提供建立、列出、刪除功能。
- `app.py`：Streamlit 介面，整合上述模組、環境依賴檢查、進度顯示與下載／清除功能。
