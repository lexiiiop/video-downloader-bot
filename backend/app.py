from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid
import threading
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
import json
import cloudscraper
import time
import requests

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create downloads directory
DOWNLOADS_DIR = Path('downloads')
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Global variables for tracking downloads
download_progress = {}
download_files = {}

INSTAGRAM_COOKIES_FILE = 'cookies_insta.txt'

# Initialize cloudscraper for Instagram requests
def get_instagram_session():
    """Create a cloudscraper session with Instagram cookies"""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    # Load Instagram cookies if available
    if os.path.exists(INSTAGRAM_COOKIES_FILE):
        cookies = {}
        with open(INSTAGRAM_COOKIES_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 7:
                        cookie_name = parts[5]
                        cookie_value = parts[6]
                        if cookie_name.startswith('#HttpOnly_'):
                            cookie_name = cookie_name[10:]
                        cookies[cookie_name] = cookie_value
        
        # Add cookies to session
        for name, value in cookies.items():
            scraper.cookies.set(name, value, domain='.instagram.com')
    
    return scraper

def is_instagram_url(url):
    """Check if URL is from Instagram"""
    return 'instagram.com' in url.lower()

def get_instagram_post_id(url):
    """Extract Instagram post ID from URL"""
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
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename[:100]

def get_video_info(url):
    """Extract video information without downloading"""
    if is_instagram_url(url):
        # Try cloudscraper first, then fallback to yt-dlp
        try:
            return get_instagram_info(url)
        except Exception as e:
            logger.warning(f"Cloudscraper failed for Instagram: {e}")
            logger.info("Trying yt-dlp as fallback for Instagram...")
            return get_instagram_info_ytdlp(url)
    
    # Use yt-dlp for other platforms
    ydl_opts = {
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        logger.info(f"Starting video info extraction for: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("yt-dlp instance created successfully")
            info = ydl.extract_info(url, download=False)
            logger.info(f"Video info extracted successfully: {info.get('title', 'Unknown')}")
            
            formats = info.get('formats', [])
            processed_formats = []
            for fmt in formats:
                if not fmt.get('ext') or fmt.get('vcodec') == 'none':
                    continue
                    
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
            
            if not processed_formats and formats:
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
    """Get Instagram post information using cloudscraper"""
    try:
        logger.info(f"Getting Instagram info for URL: {url}")
        
        # Create session with cookies
        session = get_instagram_session()
        
        # Get the post page
        response = session.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch Instagram post: {response.status_code}")
        
        # Extract video URL from page content
        content = response.text
        
        # Look for video URL patterns (updated for modern Instagram)
        video_patterns = [
            r'"video_url":"([^"]+)"',
            r'"contentUrl":"([^"]+\.mp4[^"]*)"',
            r'"video_url":"([^"]+\.mp4[^"]*)"',
            r'"video_url":"([^"]+\.mov[^"]*)"',
            r'"video_url":"([^"]+\.webm[^"]*)"',
            r'src="([^"]+\.mp4[^"]*)"',
            r'<video[^>]*src="([^"]+)"',
            r'"playbackUrl":"([^"]+)"',
            r'"mediaUrl":"([^"]+\.mp4[^"]*)"',
            r'"mediaUrl":"([^"]+\.mov[^"]*)"',
            r'"mediaUrl":"([^"]+\.webm[^"]*)"',
            r'"url":"([^"]+\.mp4[^"]*)"',
            r'"url":"([^"]+\.mov[^"]*)"',
            r'"url":"([^"]+\.webm[^"]*)"',
        ]
        
        video_url = None
        for pattern in video_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match and ('mp4' in match or 'mov' in match or 'webm' in match):
                    video_url = match
                    video_url = video_url.replace('\\u0026', '&')
                    video_url = video_url.replace('\\/', '/')
                    logger.info(f"Found video URL with pattern: {pattern}")
                    break
            if video_url:
                break
        
        if not video_url:
            # Try alternative method - get post data from Instagram API
            post_id = get_instagram_post_id(url)
            if post_id:
                logger.info(f"Trying Instagram API for post ID: {post_id}")
                api_url = f"https://www.instagram.com/p/{post_id}/?__a=1&__d=dis"
                api_response = session.get(api_url)
                if api_response.status_code == 200:
                    try:
                        data = api_response.json()
                        logger.info(f"API response keys: {list(data.keys())}")
                        
                        # Try different API response structures
                        if 'graphql' in data and 'shortcode_media' in data['graphql']:
                            media = data['graphql']['shortcode_media']
                            if media.get('is_video'):
                                video_url = media.get('video_url')
                                logger.info("Found video URL via graphql API")
                        elif 'items' in data and len(data['items']) > 0:
                            item = data['items'][0]
                            if item.get('media_type') == 2:  # Video type
                                video_url = item.get('video_versions', [{}])[0].get('url')
                                logger.info("Found video URL via items API")
                        elif 'shortcode_media' in data:
                            media = data['shortcode_media']
                            if media.get('is_video'):
                                video_url = media.get('video_url')
                                logger.info("Found video URL via shortcode_media API")
                    except Exception as e:
                        logger.error(f"Error parsing API response: {e}")
        
        if not video_url:
            # Try one more method - look for JSON-LD structured data
            json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
            json_ld_matches = re.findall(json_ld_pattern, content, re.DOTALL)
            for json_ld in json_ld_matches:
                try:
                    json_data = json.loads(json_ld)
                    if isinstance(json_data, dict):
                        # Look for video content in JSON-LD
                        if 'contentUrl' in json_data:
                            potential_url = json_data['contentUrl']
                            if any(ext in potential_url for ext in ['.mp4', '.mov', '.webm']):
                                video_url = potential_url
                                logger.info("Found video URL via JSON-LD")
                                break
                except:
                    continue
        
        if not video_url:
            # Log some debug info
            logger.error("Could not find video URL. Content preview:")
            logger.error(content[:1000])  # First 1000 chars for debugging
            raise Exception("Could not find video URL in Instagram post")
        
        # Get post caption/title
        title_patterns = [
            r'"caption":"([^"]+)"',
            r'<meta property="og:title" content="([^"]+)"',
            r'<title>([^<]+)</title>',
            r'"title":"([^"]+)"',
            r'"description":"([^"]+)"',
        ]
        
        title = "Instagram Post"
        for pattern in title_patterns:
            match = re.search(pattern, content)
            if match:
                title = match.group(1)
                title = title.replace('\\n', ' ').replace('\\r', ' ')
                title = title.replace('\\/', '/')
                if len(title) > 100:
                    title = title[:100] + "..."
                break
        
        # Create format info
        format_info = {
            'format_id': 'best',
            'ext': 'mp4',
            'filesize': 0,
            'height': 1080,
            'width': 1920,
            'format_note': 'Best Quality',
            'vcodec': 'h264',
            'acodec': 'aac',
            'has_audio': True,
            'url': video_url
        }
        
        logger.info(f"Successfully extracted Instagram video: {title}")
        return {
            'title': title,
            'duration': 0,
            'thumbnail': '',
            'formats': [format_info]
        }
        
    except Exception as e:
        logger.error(f"Error getting Instagram info: {str(e)}")
        raise Exception(f"Instagram error: {str(e)}")

def get_instagram_info_ytdlp(url):
    """Get Instagram post information using yt-dlp as fallback"""
    try:
        logger.info(f"Using yt-dlp for Instagram: {url}")
        
        ydl_opts = {
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
        }
        
        # Use Instagram cookies if available
        if os.path.exists(INSTAGRAM_COOKIES_FILE):
            ydl_opts['cookiefile'] = INSTAGRAM_COOKIES_FILE
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise Exception("yt-dlp could not extract Instagram info")
            
            # Process formats
            formats = info.get('formats', [])
            processed_formats = []
            
            for fmt in formats:
                if fmt.get('ext') in ['mp4', 'webm', 'mov']:
                    processed_formats.append({
                        'format_id': fmt.get('format_id', 'best'),
                        'ext': fmt.get('ext', 'mp4'),
                        'filesize': fmt.get('filesize', 0),
                        'height': fmt.get('height', 1080),
                        'width': fmt.get('width', 1920),
                        'format_note': fmt.get('format_note', 'Best Quality'),
                        'vcodec': fmt.get('vcodec', 'h264'),
                        'acodec': fmt.get('acodec', 'aac'),
                        'has_audio': True,
                        'url': fmt.get('url', '')
                    })
            
            if not processed_formats:
                # Create a default format
                processed_formats.append({
                    'format_id': 'best',
                    'ext': 'mp4',
                    'filesize': 0,
                    'height': 1080,
                    'width': 1920,
                    'format_note': 'Best Quality',
                    'vcodec': 'h264',
                    'acodec': 'aac',
                    'has_audio': True,
                    'url': ''
                })
            
            return {
                'title': info.get('title', 'Instagram Post'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'formats': processed_formats
            }
            
    except Exception as e:
        logger.error(f"yt-dlp fallback failed for Instagram: {str(e)}")
        raise Exception(f"Instagram error: {str(e)}")

def download_video_advanced(url, format_type, title, download_id):
    """Download video with advanced options"""
    try:
        if is_instagram_url(url):
            return download_instagram_video(url, format_type, title, download_id)
        
        # Sanitize title for filename
        safe_title = sanitize_filename(title)
        
        # Use yt-dlp for other platforms
        ydl_opts = {
            'format': format_type,
            'outtmpl': str(DOWNLOADS_DIR / f'{safe_title}.%(ext)s'),
            'progress_hooks': [lambda d: progress_hook(d, download_id)],
            'quiet': False,
            'no_warnings': False,
        }
        
        if os.path.exists('cookies.txt'):
            ydl_opts['cookiefile'] = 'cookies.txt'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        for file_path in DOWNLOADS_DIR.glob(f'{safe_title}.*'):
            if file_path.is_file():
                download_files[download_id] = str(file_path)
                download_progress[download_id] = {'status': 'completed', 'progress': 100}
                return True
        
        raise Exception("Download completed but file not found")
        
    except Exception as e:
        logger.error(f"Error in download_video_advanced: {str(e)}")
        download_progress[download_id] = {'status': 'error', 'error': str(e)}
        return False

def download_instagram_video(url, format_type, title, download_id):
    """Download Instagram video using cloudscraper"""
    try:
        logger.info(f"Downloading Instagram video: {url}")
        
        # Get video info first
        info = get_instagram_info(url)
        if not info or not info.get('formats'):
            raise Exception("Could not get video information")
        
        video_url = info['formats'][0].get('url')
        if not video_url:
            raise Exception("No video URL found")
        
        # Create session with cookies
        session = get_instagram_session()
        
        # Download the video
        response = session.get(video_url, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download video: {response.status_code}")
        
        # Sanitize title for filename
        safe_title = sanitize_filename(title)
        
        # Save the video
        file_path = DOWNLOADS_DIR / f'{safe_title}.mp4'
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        download_progress[download_id] = {
                            'status': 'downloading',
                            'progress': progress,
                            'downloaded': downloaded,
                            'total': total_size
                        }
        
        download_files[download_id] = str(file_path)
        download_progress[download_id] = {'status': 'completed', 'progress': 100}
        return True
        
    except Exception as e:
        logger.error(f"Error downloading Instagram video: {str(e)}")
        download_progress[download_id] = {'status': 'error', 'error': str(e)}
        return False

def progress_hook(d, download_id):
    """Progress hook for yt-dlp downloads"""
    if d['status'] == 'downloading':
        if 'total_bytes' in d and d['total_bytes']:
            progress = int((d['downloaded_bytes'] / d['total_bytes']) * 100)
        elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
            progress = int((d['downloaded_bytes'] / d['total_bytes_estimate']) * 100)
        else:
            progress = 0
        
        download_progress[download_id] = {
            'status': 'downloading',
            'progress': progress,
            'downloaded': d.get('downloaded_bytes', 0),
            'total': d.get('total_bytes', 0)
        }
    elif d['status'] == 'finished':
        download_progress[download_id] = {'status': 'completed', 'progress': 100}

def delete_file(download_id):
    """Delete downloaded file after serving"""
    try:
        if download_id in download_files:
            file_path = Path(download_files[download_id])
            if file_path.exists():
                file_path.unlink()
            del download_files[download_id]
        if download_id in download_progress:
            del download_progress[download_id]
    except Exception as e:
        logger.error(f"Error deleting file {download_id}: {e}")

@app.route('/api/info', methods=['POST'])
def get_info():
    """Get video information"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        logger.info(f"Analyzing URL: {url}")
        
        info = get_video_info(url)
        if info:
            return jsonify(info)
        else:
            return jsonify({'error': 'Could not extract video information'}), 400
            
    except Exception as e:
        logger.error(f"Error in get_info: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download():
    """Download video"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400
        
        url = data['url']
        format_type = data.get('format', 'best')
        title = data.get('title', 'video')
        
        download_id = str(uuid.uuid4())
        download_progress[download_id] = {'status': 'starting', 'progress': 0}
        
        def download_thread():
            download_video_advanced(url, format_type, title, download_id)
        
        thread = threading.Thread(target=download_thread)
        thread.start()
        
        return jsonify({
            'download_id': download_id,
            'status': 'started'
        })
        
    except Exception as e:
        logger.error(f"Error in download: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<download_id>', methods=['GET'])
def get_progress(download_id):
    """Get download progress"""
    try:
        if download_id in download_progress:
            return jsonify(download_progress[download_id])
        else:
            return jsonify({'error': 'Download not found'}), 404
    except Exception as e:
        logger.error(f"Error in get_progress: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<download_id>', methods=['GET'])
def serve_file(download_id):
    """Serve downloaded file"""
    try:
        if download_id not in download_files:
            return jsonify({'error': 'File not found'}), 404
        
        file_path = Path(download_files[download_id])
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        # Schedule file deletion after serving
        threading.Timer(60.0, delete_file, args=[download_id]).start()
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_path.name
        )
        
    except Exception as e:
        logger.error(f"Error in serve_file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

def cleanup_old_files():
    """Clean up old downloaded files"""
    try:
        current_time = datetime.now()
        for file_path in DOWNLOADS_DIR.glob('*'):
            if file_path.is_file():
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age > timedelta(hours=1):  # Delete files older than 1 hour
                    file_path.unlink()
    except Exception as e:
        logger.error(f"Error in cleanup: {e}")

if __name__ == '__main__':
    # Start cleanup thread
    def cleanup_thread():
        while True:
            time.sleep(300)  # Run every 5 minutes
            cleanup_old_files()
    
    cleanup_thread_instance = threading.Thread(target=cleanup_thread, daemon=True)
    cleanup_thread_instance.start()
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 
