# Video Downloader Pro

A modern web application for downloading videos from YouTube, Instagram, and other supported platforms. Built with Python Flask backend and a beautiful, responsive frontend.

## Features

- 🎥 Download videos from YouTube, Instagram, and more
- 📱 Modern, responsive UI design
- 🔍 Video information extraction
- 📊 Multiple format selection
- ⚡ Real-time download progress
- 🎨 Beautiful gradient design
- 📱 Mobile-friendly interface

## Tech Stack

### Backend
- **Python Flask** - Web framework
- **yt-dlp** - Video download library
- **Flask-CORS** - Cross-origin resource sharing

### Frontend
- **HTML5** - Structure
- **CSS3** - Modern styling with gradients and animations
- **JavaScript (ES6+)** - Interactive functionality
- **Font Awesome** - Icons
- **Google Fonts** - Typography

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - **Windows:**
   ```bash
   venv\Scripts\activate
   ```
   - **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the Flask application:
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Open `index.html` in your web browser or serve it using a local server:
   - **Using Python:**
   ```bash
   python -m http.server 8000
   ```
   - **Using Node.js (if installed):**
   ```bash
   npx serve .
   ```

The frontend will be available at `http://localhost:8000`

## Usage

1. Open the application in your web browser
2. Paste a video URL from YouTube, Instagram, or other supported platforms
3. Click "Analyze" to extract video information
4. Select your preferred format and quality
5. Click "Download" to start the download process
6. Once complete, click "Download File" to save the video to your device

## Supported Platforms

- YouTube
- Instagram
- Facebook
- Twitter
- TikTok
- Vimeo
- And many more (via yt-dlp)

## API Endpoints

- `POST /api/info` - Get video information
- `POST /api/download` - Download video
- `GET /api/download-file/<filename>` - Serve downloaded file
- `GET /api/health` - Health check

## Project Structure

```
video-downloader-app/
├── backend/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   └── downloads/          # Downloaded files (created automatically)
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── styles.css          # CSS styles
│   └── script.js           # JavaScript functionality
└── README.md               # This file
```

## Configuration

### Backend Configuration

The Flask application runs on `http://localhost:5000` by default. You can modify the port and host in `backend/app.py`:

```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Frontend Configuration

The frontend expects the backend to be running on `http://localhost:5000`. If you change the backend URL, update the `apiBase` in `frontend/script.js`:

```javascript
this.apiBase = 'http://localhost:5000/api';
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure the backend is running and CORS is properly configured
2. **Download Failures**: Check if the video URL is valid and accessible
3. **Format Issues**: Some videos may not have all formats available

### Debug Mode

The Flask application runs in debug mode by default. Check the console for detailed error messages.

## Security Notes

- This application is for educational purposes
- Always respect copyright laws and terms of service
- Downloaded files are stored temporarily on the server
- Consider implementing user authentication for production use

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for educational purposes only. Users are responsible for ensuring they have the right to download any content and must comply with applicable laws and terms of service. 