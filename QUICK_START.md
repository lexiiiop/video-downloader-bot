# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Start the Backend
```bash
# Option A: Use the batch file (Windows)
start_backend.bat

# Option B: Manual start
cd backend
pip install -r requirements.txt
python app.py
```

### Step 2: Start the Frontend
```bash
# Option A: Use the batch file (Windows)
start_frontend.bat

# Option B: Manual start
cd frontend
python -m http.server 8000
```

### Step 3: Open the Application
Open your web browser and go to: **http://localhost:8000**

## 🎯 How to Use

1. **Paste a video URL** from YouTube, Instagram, or other supported platforms
2. **Click "Analyze"** to extract video information
3. **Select your preferred format** and quality
4. **Click "Download"** to start the download
5. **Click "Download File"** to save the video to your device

## 🔧 Troubleshooting

### Backend Issues
- Make sure Python 3.7+ is installed
- Check if port 5000 is available
- Run `python test_app.py` in the backend directory to test

### Frontend Issues
- Make sure the backend is running on port 5000
- Check browser console for CORS errors
- Try refreshing the page

### Common Errors
- **"Backend server is not running"**: Start the backend first
- **"CORS error"**: Make sure both servers are running
- **"Download failed"**: Check the video URL and try again

## 📱 Supported Platforms
- YouTube ✅
- Instagram ✅
- Facebook ✅
- Twitter ✅
- TikTok ✅
- Vimeo ✅
- And many more!

## 🎨 Features
- Modern, responsive design
- Multiple format selection
- Real-time progress tracking
- Mobile-friendly interface
- Beautiful gradient UI

## ⚡ Quick Test
Try this YouTube URL to test the application:
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Happy downloading! 🎥✨ 