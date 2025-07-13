import json
import yt_dlp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                            'has_audio': has_audio,
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

def handler(request):
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': ''
        }
    
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request body
        body = json.loads(request.body)
        url = body.get('url')
        
        if not url:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'URL is required'})
            }
        
        logger.info(f"Analyzing URL: {url}")
        info = get_video_info(url)
        
        if info:
            logger.info(f"Found {len(info.get('formats', []))} formats for video: {info.get('title', 'Unknown')}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(info)
            }
        else:
            logger.error("Could not extract video information")
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Could not extract video information'})
            }
            
    except Exception as e:
        logger.error(f"Error in get_info: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        } 