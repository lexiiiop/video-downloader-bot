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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import cloudscraper
import time

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

# Initialize Selenium WebDriver for Instagram scraping
def get_webdriver():
    """Get configured Chrome WebDriver for Instagram scraping"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        return None

# Initialize cloudscraper for API requests
scraper = cloudscraper.create_scraper()

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
        return get_instagram_info(url)
    
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
    """Get Instagram post information using Selenium"""
    try:
        driver = get_webdriver()
        if not driver:
            raise Exception("Failed to initialize WebDriver")
        
        logger.info(f"Getting Instagram info for URL: {url}")
        
        # Load cookies if available
        if os.path.exists(INSTAGRAM_COOKIES_FILE):
            driver.get("https://www.instagram.com")
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
            
            for name, value in cookies.items():
                driver.add_cookie({'name': name, 'value': value})
        
        # Navigate to the post
        driver.get(url)
        time.sleep(3)  # Wait for page to load
        
        # Check if it's a video post
        try:
            video_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            video_url = video_element.get_attribute('src')
            
            if not video_url:
                raise Exception("This Instagram post does not contain a video")
            
            # Get post caption
            try:
                caption_element = driver.find_element(By.CSS_SELECTOR, 'h1, ._a9zs')
                caption = caption_element.text
            except:
                caption = "Instagram Post"
            
            # Get username
            try:
                username_element = driver.find_element(By.CSS_SELECTOR, 'a[href*="/p/"]')
                username = username_element.text
            except:
                username = "unknown"
            
            # Get thumbnail
            try:
                img_element = driver.find_element(By.CSS_SELECTOR, 'img[src*="instagram"]')
                thumbnail = img_element.get_attribute('src')
            except:
                thumbnail = ""
            
            format_info = {
                'format_id': 'best',
                'ext': 'mp4',
                'filesize': 0,
                'height': 0,
                'width': 0,
                'format_note': 'Instagram Video',
                'vcodec': 'h264',
                'acodec': 'aac',
                'has_audio': True,
            }
            
            return {
                'title': caption,
                'duration': 0,
                'thumbnail': thumbnail,
                'formats': [format_info],
                'platform': 'instagram',
                'post_id': get_instagram_post_id(url),
                'owner_username': username,
                'video_url': video_url
            }
            
        except Exception as e:
            raise Exception(f"Could not find video in Instagram post: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error getting Instagram info: {str(e)}")
        raise Exception(f"Instagram error: {str(e)}")
    finally:
        if driver:
            driver.quit()

def download_video_advanced(url, format_type, title, download_id):
    """Download video with advanced format options"""
    if is_instagram_url(url):
        return download_instagram_video(url, format_type, title, download_id)
    
    # Use yt-dlp for other platforms
    safe_title = sanitize_filename(title)
    unique_id = str(uuid.uuid4())[:8]
    output_template = str(DOWNLOADS_DIR / f"{safe_title}_{unique_id}.%(ext)s")
    
    ydl_opts = {
        'outtmpl': output_template,
        'progress_hooks': [lambda d: progress_hook(d, download_id)],
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    if format_type == 'best':
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif format_type == 'video':
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif format_type == 'audio':
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format_type == 'video_only':
        ydl_opts['format'] = 'bestvideo[ext=mp4]/bestvideo'
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            downloaded_files = list(DOWNLOADS_DIR.glob(f"{safe_title}_{unique_id}.*"))
            if downloaded_files:
                file_path = str(downloaded_files[0])
                
                download_files[download_id] = {
                    'file_path': file_path,
                    'filename': os.path.basename(file_path),
                    'file_size': os.path.getsize(file_path),
                    'created_at': datetime.now(),
                    'title': title,
                    'format_type': format_type
                }
                
                download_progress[download_id]['completed'] = True
                download_progress[download_id]['progress'] = 100
                download_progress[download_id]['status'] = 'Download completed!'
                
                threading.Timer(1800, delete_file, args=[download_id]).start()
                
                return file_path
            else:
                raise Exception("Downloaded file not found")
    except Exception as e:
        logger.error(f"Error downloading video: {str(e)}")
        download_progress[download_id]['error'] = str(e)
        raise

def download_instagram_video(url, format_type, title, download_id):
    """Download Instagram video using Selenium"""
    try:
        driver = get_webdriver()
        if not driver:
            raise Exception("Failed to initialize WebDriver")
        
        logger.info(f"Downloading Instagram video for URL: {url}")
        
        # Load cookies if available
        if os.path.exists(INSTAGRAM_COOKIES_FILE):
            driver.get("https://www.instagram.com")
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
            
            for name, value in cookies.items():
                driver.add_cookie({'name': name, 'value': value})
        
        # Navigate to the post
        driver.get(url)
        time.sleep(3)
        
        # Find video element
        video_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
        video_url = video_element.get_attribute('src')
        
        if not video_url:
            raise Exception("This Instagram post does not contain a video")
        
        # Download the video
        safe_title = sanitize_filename(title)
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{safe_title}_{unique_id}.mp4"
        file_path = str(DOWNLOADS_DIR / filename)
        
        # Use cloudscraper to download the video
        response = scraper.get(video_url, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
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
        
        return file_path
        
    except Exception as e:
        logger.error(f"Error downloading Instagram video: {str(e)}")
        download_progress[download_id]['error'] = str(e)
        raise
    finally:
        if driver:
            driver.quit()

def progress_hook(d, download_id):
    """Progress hook for yt-dlp downloads"""
    if download_id in download_progress:
        if d['status'] == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    progress = int((downloaded / total) * 100)
                    download_progress[download_id]['progress'] = progress
                    download_progress[download_id]['status'] = f"Downloading... {progress}%"
            except:
                pass
        elif d['status'] == 'finished':
            download_progress[download_id]['status'] = 'Processing...'

def delete_file(download_id):
    """Delete file after specified time"""
    if download_id in download_files:
        try:
            file_path = download_files[download_id]['file_path']
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
        finally:
            # Clean up tracking
            if download_id in download_files:
                del download_files[download_id]
            if download_id in download_progress:
                del download_progress[download_id]

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