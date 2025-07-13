from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid
from pathlib import Path
import logging

app = Flask(__name__)

# Configure CORS for production
if os.environ.get('FLASK_ENV') == 'production':
    CORS(app, origins=['*'])  # Allow all origins for now
else:
    CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create downloads directory
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

def get_video_info(url):
    """Extract video information without downloading"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get all available formats
            formats = info.get('formats', [])
            
            # Filter and process formats
            processed_formats = []
            for fmt in formats:
                # Skip formats without extension or with audio-only
                if not fmt.get('ext') or fmt.get('vcodec') == 'none':
                    continue
                    
                # Include common video formats
                if fmt.get('ext') in ['mp4', 'webm', 'mkv', 'avi', 'mov', 'flv', '3gp']:
                    has_audio = fmt.get('acodec') and fmt.get('acodec') != 'none'
                    processed_formats.append({
                        'format_id': fmt.get('format_id', ''),
                        'ext': fmt.get('ext', ''),
                        'filesize': fmt.get('filesize', 0),
                        'height': fmt.get('height', 0),
                        'width': fmt.get('width', 0),
                        'format_note': fmt.get('format_note', ''),
                        'vcodec': fmt.get('vcodec', ''),
                        'acodec': fmt.get('acodec', ''),
                        'has_audio': has_audio,
                    })
            
            # If no formats found, try to get at least one format
            if not processed_formats and formats:
                # Take the first format with video
                for fmt in formats:
                    if fmt.get('vcodec') and fmt.get('vcodec') != 'none':
                        processed_formats.append({
                            'format_id': fmt.get('format_id', ''),
                            'ext': fmt.get('ext', ''),
                            'filesize': fmt.get('filesize', 0),
                            'height': fmt.get('height', 0),
                            'width': fmt.get('width', 0),
                            'format_note': fmt.get('format_note', ''),
                            'vcodec': fmt.get('vcodec', ''),
                            'acodec': fmt.get('acodec', ''),
                        })
                        break
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'formats': processed_formats
            }
    except Exception as e:
        logger.error(f"Error extracting video info: {str(e)}")
        return None

def download_video(url, format_id=None):
    """Download video with specified format"""
    # Generate unique filename
    unique_id = str(uuid.uuid4())
    output_template = str(DOWNLOADS_DIR / f"{unique_id}.%(ext)s")
    
    ydl_opts = {
        'outtmpl': output_template,
        'progress_hooks': [],
        'merge_output_format': 'mp4',
    }
    
    if format_id:
        # For specific format, try to get it with audio
        ydl_opts['format'] = f'{format_id}+bestaudio/best'
    else:
        # For best quality, get best video with audio
        ydl_opts['format'] = 'best[ext=mp4]/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Find the downloaded file
            downloaded_files = list(DOWNLOADS_DIR.glob(f"{unique_id}.*"))
            if downloaded_files:
                return str(downloaded_files[0])
            else:
                raise Exception("Downloaded file not found")
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        raise

@app.route('/api/info', methods=['POST'])
def get_info():
    """Get video information"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Analyzing URL: {url}")
        info = get_video_info(url)
        
        if info:
            logger.info(f"Found {len(info.get('formats', []))} formats for video: {info.get('title', 'Unknown')}")
            return jsonify(info)
        else:
            logger.error("Could not extract video information")
            return jsonify({'error': 'Could not extract video information'}), 400
            
    except Exception as e:
        logger.error(f"Error in get_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download():
    """Download video"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_id = data.get('format_id')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Downloading URL: {url} with format: {format_id}")
        
        # Download the video
        file_path = download_video(url, format_id)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        logger.info(f"Download completed: {file_name} ({file_size} bytes)")
        
        return jsonify({
            'success': True,
            'file_path': file_path,
            'file_name': file_name,
            'file_size': file_size
        })
        
    except Exception as e:
        logger.error(f"Error in download: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-file/<filename>', methods=['GET'])
def download_file(filename):
    """Serve downloaded file"""
    try:
        file_path = DOWNLOADS_DIR / filename
        if file_path.exists():
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port) 