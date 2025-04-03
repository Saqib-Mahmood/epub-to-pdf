@echo off
setlocal enabledelayedexpansion

REM === CONFIGURATION ===
set APP_NAME=epub_to_pdf_converter
set MAIN_SCRIPT=epub_to_pdf_gui.py
set ICON_PNG=icon.png
set ICON_ICO=app_icon.ico
set LOGFILE=build_log.txt

echo 🚀 Starting EPUB to PDF Converter - RELEASE Build... > %LOGFILE%

REM Step 1: Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt >> %LOGFILE% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to install dependencies. See %LOGFILE%
    pause
    exit /b 1
)

REM Step 2: Install pyinstaller (if missing)
pip show pyinstaller >> %LOGFILE% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo 📦 Installing PyInstaller...
    pip install pyinstaller >> %LOGFILE% 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install PyInstaller. See %LOGFILE%
        pause
        exit /b 1
    )
)

REM Step 3: Convert PNG to .ICO
IF NOT EXIST %ICON_ICO% (
    echo 🎨 Converting %ICON_PNG% to %ICON_ICO%...
    python -c "from PIL import Image; Image.open('%ICON_PNG%').save('%ICON_ICO%', format='ICO', sizes=[(64,64)])" >> %LOGFILE% 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to convert PNG to ICO. See %LOGFILE%
        pause
        exit /b 1
    )
)

REM Step 4: Build EXE
echo 🔨 Building EXE with PyInstaller...
python -m PyInstaller --onefile --noconsole --icon=%ICON_ICO% --name %APP_NAME% %MAIN_SCRIPT% >> %LOGFILE% 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ PyInstaller build failed. See %LOGFILE%
    pause
    exit /b 1
)

REM Step 5: Cleanup
echo 🧹 Cleaning up build artifacts...
IF EXIST build rmdir /s /q build
IF EXIST %APP_NAME%.spec del %APP_NAME%.spec

echo ✅ Build Complete! Your EXE is located at: dist\%APP_NAME%.exe
pause
