# sanchuan-app

三川工方工程管理系統。

## 施工前後模擬（`simulator.html`）

單一檔案、免安裝，用瀏覽器直接開啟即可使用。上傳工地現況照片，在照片上塗抹要更換材質的範圍，再上傳木皮／材質色板，由 Google Gemini 生成模擬圖並提供前後對比。

### 使用步驟

1. 開啟 `simulator.html`，點右上角「設定金鑰」貼上 Google Gemini API 金鑰
   （到 [aistudio.google.com/apikey](https://aistudio.google.com/apikey) 免費申請）。
   金鑰只存在瀏覽器的 localStorage，不會上傳到任何伺服器。
2. **上傳現況照片** — 建議正對牆面拍攝、光線平均。
3. **塗抹選取範圍** — 用手指或滑鼠直接在照片上塗抹要換材質的部位（櫃體門片、牆板等），
   塗到的地方顯示金色。可切換擦除、調整筆刷粗細、復原、全選。
4. **上傳木皮色板**，需要時補充材質描述（霧面／直紋／深胡桃）與部位名稱。
5. **開始模擬** — 完成後拖曳中間滑桿比較施工前後，可下載模擬圖。

### 模型選擇

| 選項 | 模型 ID | 說明 |
| --- | --- | --- |
| Nano Banana Pro | `gemini-3-pro-image-preview` | 畫質最好，單價較高 |
| Nano Banana 2 | `gemini-3.1-flash-image-preview` | 預設，速度快、成本低 |
| Nano Banana | `gemini-2.5-flash-image` | 舊版 |

### 「鎖定未選取區域」

預設開啟。開啟時只會把 AI 產生的像素套用在塗抹範圍內（邊緣做羽化銜接），
範圍以外的畫面直接沿用原照片，確保牆面、地板、家具不會被模型順手改掉。
關閉則直接使用 AI 的完整輸出。
