@echo off
setlocal

echo ============================================
echo   Music Vocal Separator - Install
echo   音樂人聲分離工具 - 安裝程式
echo ============================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [錯誤] 找不到 Python，請先安裝 Python 3.11：
    echo   https://www.python.org/downloads/
    echo 安裝時請務必勾選 "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

python --version

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo.
    echo [警告] 找不到 FFmpeg，請擇一方式安裝：
    echo   1. winget install --id Gyan.FFmpeg -e
    echo   2. choco install ffmpeg
    echo   3. 手動下載 https://www.gyan.dev/ffmpeg/builds/
    echo      解壓縮後將其中的 bin 資料夾路徑加入系統環境變數 PATH
    echo 安裝完成後請重新開啟命令提示字元，再重新執行本安裝程式。
    echo.
    pause
) else (
    echo [OK] 已偵測到 FFmpeg
)

echo.
if not exist ".venv" (
    echo 建立虛擬環境中...
    python -m venv .venv
    if errorlevel 1 (
        echo [錯誤] 建立虛擬環境失敗
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo 升級 pip...
python -m pip install --upgrade pip

echo.
echo 安裝套件中（首次安裝視網路速度可能需要數分鐘，torch/demucs 檔案較大）...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [錯誤] 套件安裝失敗，請檢查上方錯誤訊息與網路連線後再試一次。
    pause
    exit /b 1
)

echo.
echo ============================================
echo   安裝完成！請執行 start.bat 啟動程式。
echo ============================================
pause
