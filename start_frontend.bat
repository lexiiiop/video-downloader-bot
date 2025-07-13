@echo off
echo Starting Video Downloader Frontend...
echo.
cd frontend
echo Starting HTTP server...
python -m http.server 8000
pause 