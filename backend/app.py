from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import instaloader
import os
import tempfile
import uuid
import threading
import time
from pathlib import Path
import logging
import re
from datetime import datetime, timedelta

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

# Store download progress and file info
download_progress = {}
download_files = {}

# Initialize Instaloader instance
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    dirname_pattern=str(DOWNLOADS_DIR)
)

INSTAGRAM_COOKIES_FILE = 'cookies_insta.txt'

# Load Instagram cookies if available
if os.path.exists(INSTAGRAM_COOKIES_FILE):
    try:
        # Parse cookies from file and load them properly
        cookies = {}
        with open(INSTAGRAM_COOKIES_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        cookie_name = parts[5]
                        cookie_value = parts[6]
                        cookies[cookie_name] = cookie_value
        
        # Load session with proper cookies
        if 'sessionid' in cookies and cookies['sessionid']:
            L.load_session_from_file('instagram_session', cookies)
            logger.info("Loaded Instagram session with cookies from file")
        else:
            logger.warning("No valid sessionid found in cookies file")
    except Exception as e:
        logger.warning(f"Could not load Instagram cookies: {e}")

def is_instagram_url(url):
    """Check if URL is from Instagram"""
    return 'instagram.com' in url.lower()

def get_instagram_post_id(url):
    """Extract Instagram post ID from URL"""
    # Handle different Instagram URL formats
    patterns = [
        r'instagram.com/p/([^/]+)',
        r'instagram.com/reel/([^/]+)',
        r'instagram.com/tv/([^/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def sanitize_filename(filename):
    """Sanitize filename for safe file system usage"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and limit length
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename[:100]  # Limit to 100 characters

def get_video_info(url):
    """Extract video information without downloading"""
    # Check if it's an Instagram URL
    if is_instagram_url(url):
        return get_instagram_info(url)
    
    # Use yt-dlp for other platforms
    ydl_opts = {
        'quiet': False,  # Enable logging for debugging
        'no_warnings': False,  # Show warnings
        'extract_flat': False,
    }
    
    # Only use cookies if the file exists
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        logger.info(f"Starting video info extraction for: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("yt-dlp instance created successfully")
            info = ydl.extract_info(url, download=False)
            logger.info(f"Video info extracted successfully: {info.get('title', 'Unknown')}")
            
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

def get_instagram_info(url):
    """Get Instagram post information"""
    try:
        post_id = get_instagram_post_id(url)
        if not post_id:
            raise Exception("Could not extract Instagram post ID from URL")
        
        logger.info(f"Getting Instagram info for post ID: {post_id}")
        
        # Try to load session if available
        if os.path.exists('instagram_session'):
            try:
                L.load_session_from_file('instagram_session')
                logger.info("Loaded Instagram session from file")
            except Exception as e:
                logger.warning(f"Could not load Instagram session: {e}")
        # Get post info
        try:
            post = instaloader.Post.from_shortcode(L.context, post_id)
        except Exception as post_error:
            if "401" in str(post_error) or "Unauthorized" in str(post_error):
                logger.error("Instagram authentication failed. Please check your session.")
                raise Exception("Instagram authentication failed. Please try creating a new session or check your cookies.")
            else:
                raise post_error
        
        # Check if post has video
        if not post.is_video:
            raise Exception("This Instagram post does not contain a video")
        
        # Get video info
        video_url = post.video_url
        video_size = post.video_filesize if hasattr(post, 'video_filesize') else 0
        
        # Create format info similar to yt-dlp
        format_info = {
            'format_id': 'best',
            'ext': 'mp4',
            'filesize': video_size,
            'height': post.video_height if hasattr(post, 'video_height') else 0,
            'width': post.video_width if hasattr(post, 'video_width') else 0,
            'format_note': 'Instagram Video',
            'vcodec': 'h264',
            'acodec': 'aac',
            'has_audio': True,
        }
        
        return {
            'title': f"Instagram Post by {post.owner_username}",
            'duration': 0,  # Instagram doesn't provide duration
            'thumbnail': post.url if hasattr(post, 'url') else '',
            'formats': [format_info],
            'platform': 'instagram',
            'post_id': post_id,
            'owner_username': post.owner_username
        }
        
    except Exception as e:
        logger.error(f"Error getting Instagram info: {str(e)}")
        raise Exception(f"Instagram error: {str(e)}")

def download_video_advanced(url, format_type, title, download_id):
    """Download video with advanced format options"""
    # Check if it's an Instagram URL
    if is_instagram_url(url):
        return download_instagram_video(url, format_type, title, download_id)
    
    # Use yt-dlp for other platforms
    # Sanitize title for filename
    safe_title = sanitize_filename(title)
    
    # Generate unique filename with title
    unique_id = str(uuid.uuid4())[:8]
    output_template = str(DOWNLOADS_DIR / f"{safe_title}_{unique_id}.%(ext)s")
    
    ydl_opts = {
        'outtmpl': output_template,
        'progress_hooks': [lambda d: progress_hook(d, download_id)],
    }
    
    # Only use cookies if the file exists
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    # Configure format based on type - use simpler formats that don't require FFmpeg
    if format_type == 'best':
        # Best quality that includes audio (single format)
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif format_type == 'video':
        # High quality video with audio (single format)
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif format_type == 'audio':
        # Audio only in best quality
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format_type == 'video_only':
        # Ultra HD video without audio (single format)
        ydl_opts['format'] = 'bestvideo[ext=mp4]/bestvideo'
    else:
        # Default to best quality
        ydl_opts['format'] = 'best[ext=mp4]/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the downloaded file
            downloaded_files = list(DOWNLOADS_DIR.glob(f"{safe_title}_{unique_id}.*"))
            if downloaded_files:
                file_path = str(downloaded_files[0])
                
                # Update download info
                download_files[download_id] = {
                    'file_path': file_path,
                    'filename': os.path.basename(file_path),
                    'file_size': os.path.getsize(file_path),
                    'created_at': datetime.now(),
                    'title': title,
                    'format_type': format_type
                }
                
                # Mark as completed
                download_progress[download_id]['completed'] = True
                download_progress[download_id]['progress'] = 100
                download_progress[download_id]['status'] = 'Download completed!'
                
                # Schedule file deletion after 30 minutes
                threading.Timer(1800, delete_file, args=[download_id]).start()
                
                return file_path
            else:
                raise Exception("Downloaded file not found")
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        download_progress[download_id]['error'] = str(e)
        raise

def download_instagram_video(url, format_type, title, download_id):
    """Download Instagram video using Instaloader"""
    try:
        post_id = get_instagram_post_id(url)
        if not post_id:
            raise Exception("Could not extract Instagram post ID from URL")
        
        logger.info(f"Downloading Instagram video for post ID: {post_id}")
        
        # Update progress
        download_progress[download_id]['status'] = 'Connecting to Instagram...'
        download_progress[download_id]['progress'] = 10
        
        # Try to load session if available
        if os.path.exists('instagram_session'):
            try:
                L.load_session_from_file('instagram_session')
                logger.info("Loaded Instagram session from file")
            except Exception as e:
                logger.warning(f"Could not load Instagram session: {e}")
        # Get post
        download_progress[download_id]['status'] = 'Getting post information...'
        download_progress[download_id]['progress'] = 30
        
        try:
            post = instaloader.Post.from_shortcode(L.context, post_id)
        except Exception as post_error:
            if "401" in str(post_error) or "Unauthorized" in str(post_error):
                logger.error("Instagram authentication failed during download. Please check your session.")
                raise Exception("Instagram authentication failed. Please try creating a new session or check your cookies.")
            else:
                raise post_error
        
        if not post.is_video:
            raise Exception("This Instagram post does not contain a video")
        
        # Update progress
        download_progress[download_id]['status'] = 'Preparing download...'
        download_progress[download_id]['progress'] = 50
        
        # Generate filename
        safe_title = sanitize_filename(title)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{safe_title}_{unique_id}.mp4"
        file_path = str(DOWNLOADS_DIR / filename)
        
        # Download video
        download_progress[download_id]['status'] = 'Downloading video...'
        download_progress[download_id]['progress'] = 70
        
        # Download the video file directly
        import requests
        video_response = requests.get(post.video_url, stream=True)
        video_response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Update progress
        download_progress[download_id]['status'] = 'Processing...'
        download_progress[download_id]['progress'] = 90
        
        # Update download info
        download_files[download_id] = {
            'file_path': file_path,
            'filename': filename,
            'file_size': os.path.getsize(file_path),
            'created_at': datetime.now(),
            'title': title,
            'format_type': format_type,
            'platform': 'instagram'
        }
        
        # Mark as completed
        download_progress[download_id]['completed'] = True
        download_progress[download_id]['progress'] = 100
        download_progress[download_id]['status'] = 'Download completed!'
        
        # Schedule file deletion after 30 minutes
        threading.Timer(1800, delete_file, args=[download_id]).start()
        
        logger.info(f"Instagram video downloaded successfully: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error downloading Instagram video: {str(e)}")
        download_progress[download_id]['error'] = str(e)
        raise

def progress_hook(d, download_id):
    """Progress hook for yt-dlp"""
    if download_id in download_progress:
        if d['status'] == 'downloading':
            # Calculate progress percentage
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                progress = min(int((downloaded / total) * 100), 99)
                download_progress[download_id]['progress'] = progress
                download_progress[download_id]['status'] = f'Downloading... {progress}%'
            else:
                download_progress[download_id]['status'] = 'Downloading...'
        
        elif d['status'] == 'finished':
            download_progress[download_id]['status'] = 'Processing...'
            download_progress[download_id]['progress'] = 95

def delete_file(download_id):
    """Delete file after 30 minutes"""
    if download_id in download_files:
        file_info = download_files[download_id]
        file_path = file_info['file_path']
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        # Clean up tracking data
        download_files.pop(download_id, None)
        download_progress.pop(download_id, None)

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
    """Download video with advanced format options"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'best')
        title = data.get('title', 'video')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Generate download ID
        download_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        download_progress[download_id] = {
            'progress': 0,
            'status': 'Initializing...',
            'completed': False,
            'error': None
        }
        
        logger.info(f"Starting download: {url} with format: {format_type}")
        
        # Start download in background thread
        def download_thread():
            try:
                download_video_advanced(url, format_type, title, download_id)
            except Exception as e:
                logger.error(f"Download thread error: {str(e)}")
                download_progress[download_id]['error'] = str(e)
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'download_id': download_id,
            'status': 'Download started'
        })
        
    except Exception as e:
        logger.error(f"Error in download: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<download_id>', methods=['GET'])
def get_progress(download_id):
    """Get download progress"""
    try:
        if download_id not in download_progress:
            return jsonify({'error': 'Download not found'}), 404
        
        progress_info = download_progress[download_id]
        
        if progress_info.get('error'):
            return jsonify({'error': progress_info['error']}), 400
        
        response = {
            'progress': progress_info.get('progress', 0),
            'status': progress_info.get('status', 'Unknown'),
            'completed': progress_info.get('completed', False)
        }
        
        # If completed, include file info
        if progress_info.get('completed') and download_id in download_files:
            file_info = download_files[download_id]
            response.update({
                'filename': file_info['filename'],
                'file_size': file_info['file_size'],
                'title': file_info['title']
            })
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<download_id>', methods=['GET'])
def serve_file(download_id):
    """Serve downloaded file"""
    try:
        if download_id not in download_files:
            return jsonify({'error': 'File not found'}), 404
        
        file_info = download_files[download_id]
        file_path = file_info['file_path']
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on disk'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_info['filename']
        )
        
    except Exception as e:
        logger.error(f"Error serving file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/instagram/session', methods=['POST'])
def create_instagram_session():
    """Create Instagram session for authenticated downloads"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        logger.info(f"Creating Instagram session for user: {username}")
        
        # Login to Instagram
        L.login(username, password)
        
        # Test login to ensure it worked
        try:
            test_user = L.test_login()
            logger.info(f"Login test successful for user: {test_user}")
        except Exception as test_error:
            logger.warning(f"Login test failed: {test_error}")
            # Continue anyway as the login might still work
        
        # Save session
        L.save_session_to_file('instagram_session')
        
        logger.info("Instagram session created successfully")
        return jsonify({'message': 'Instagram session created successfully'})
        
    except Exception as e:
        logger.error(f"Error creating Instagram session: {str(e)}")
        return jsonify({'error': f'Failed to create session: {str(e)}'}), 500

@app.route('/api/instagram/test', methods=['GET'])
def test_instagram_session():
    """Test Instagram session authentication"""
    try:
        # Try to test login
        test_user = L.test_login()
        return jsonify({
            'status': 'authenticated',
            'username': test_user,
            'message': 'Instagram session is valid'
        })
    except Exception as e:
        logger.error(f"Instagram session test failed: {str(e)}")
        return jsonify({
            'status': 'not_authenticated',
            'error': str(e),
            'message': 'Instagram session is invalid or expired'
        }), 401

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

# Cleanup old files on startup
def cleanup_old_files():
    """Clean up files older than 30 minutes"""
    cutoff_time = datetime.now() - timedelta(minutes=30)
    
    for file_path in DOWNLOADS_DIR.glob('*'):
        try:
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    logger.info(f"Cleaned up old file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")

# Run cleanup on startup
cleanup_old_files()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 