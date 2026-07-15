@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\activate.bat" (
    echo 尚未安裝，請先執行 install.bat
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo [警告] 找不到 FFmpeg，程式啟動後將於畫面上提示安裝方式。
)

echo 啟動 音樂人聲分離工具 …
echo 瀏覽器將自動開啟 http://localhost:8501
echo 若要結束程式，請關閉此視窗或按 Ctrl+C
echo.

streamlit run app.py

pause
