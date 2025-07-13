# YouTube Cookie Export Guide

## Why Cookies Are Needed
YouTube requires authentication for many videos, especially age-restricted content. The `cookies.txt` file allows yt-dlp to access these videos.

## How to Export Fresh Cookies

### Method 1: Using Browser Extensions (Recommended)

#### For Chrome/Edge:
1. Install the "Get cookies.txt" extension
2. Go to YouTube and make sure you're logged in
3. Click the extension icon
4. Click "Export" to download cookies.txt
5. Place the file in the `backend` directory

#### For Firefox:
1. Install the "cookies.txt" extension
2. Go to YouTube and make sure you're logged in
3. Click the extension icon
4. Click "Export" to download cookies.txt
5. Place the file in the `backend` directory

### Method 2: Manual Export (Advanced)

#### Using curl (if you have browser dev tools):
1. Open YouTube in your browser
2. Open Developer Tools (F12)
3. Go to Network tab
4. Navigate to any YouTube page
5. Find a request to youtube.com
6. Copy the Cookie header value
7. Create a cookies.txt file with the format:
   ```
   .youtube.com	TRUE	/	TRUE	1735689600	VISITOR_INFO1_LIVE	[value]
   .youtube.com	TRUE	/	TRUE	1735689600	LOGIN_INFO	[value]
   ```

## Important Notes

- **Cookie Rotation**: YouTube rotates cookies regularly for security
- **Re-export**: You may need to re-export cookies every few days/weeks
- **Privacy**: Keep your cookies.txt file private and never share it
- **Location**: The cookies.txt file must be in the `backend` directory

## Troubleshooting

### Cookie Warnings
If you see warnings about invalid cookies:
1. Re-export fresh cookies from your browser
2. Make sure you're logged into YouTube
3. Try accessing the video in your browser first

### No Cookies File
If you don't have a cookies.txt file:
- The app will still work for public videos
- Age-restricted or private videos may fail
- You'll see warnings but downloads will continue

## Security Best Practices

1. **Never commit cookies.txt to git** (it's already in .gitignore)
2. **Use environment variables** for production deployments
3. **Rotate cookies regularly**
4. **Monitor for unauthorized access**

## Production Deployment

For production deployments, consider:
- Using environment variables for cookie data
- Implementing secure cookie storage
- Regular cookie rotation schedules
- Monitoring for cookie expiration 