# Video Downloader Bot - Deployment Guide

## Overview
This guide will help you deploy your video downloader bot to:
- **Frontend**: Netlify (static hosting)
- **Backend**: Railway (Python Flask app)

## Prerequisites
1. GitHub account
2. Netlify account (free)
3. Railway account (free tier available)

## Step 1: Prepare Your Repository

### 1.1 Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/video-downloader-bot.git
git push -u origin main
```

## Step 2: Deploy Backend to Railway

### 2.1 Connect to Railway
1. Go to [Railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `video-downloader-bot` repository
6. Select the `backend` directory as the source

### 2.2 Configure Environment Variables
In Railway dashboard, add these environment variables:
```
PORT=5000
FLASK_ENV=production
```

### 2.3 Deploy
1. Railway will automatically detect it's a Python app
2. It will install dependencies from `requirements.txt`
3. Deploy using the `Procfile` or `railway.json` configuration

### 2.4 Get Your Backend URL
After deployment, Railway will provide a URL like:
`https://your-app-name.railway.app`

## Step 3: Deploy Frontend to Netlify

### 3.1 Connect to Netlify
1. Go to [Netlify.com](https://netlify.com)
2. Sign in with GitHub
3. Click "New site from Git"
4. Choose your `video-downloader-bot` repository
5. Set build settings:
   - **Build command**: (leave empty)
   - **Publish directory**: `frontend`

### 3.2 Update Frontend API Endpoint
Before deploying, update the API endpoint in `frontend/script.js`:

```javascript
// Change this line in script.js
this.apiBase = 'https://your-railway-app-url.railway.app/api';
```

### 3.3 Deploy
1. Click "Deploy site"
2. Netlify will build and deploy your frontend
3. You'll get a URL like: `https://your-site-name.netlify.app`

## Step 4: Test Your Deployment

### 4.1 Test Backend
Visit: `https://your-railway-app-url.railway.app/api/health`
Should return: `{"status": "healthy"}`

### 4.2 Test Frontend
Visit your Netlify URL and try downloading a video.

## Step 5: Custom Domain (Optional)

### 5.1 Netlify Custom Domain
1. In Netlify dashboard, go to "Domain settings"
2. Add your custom domain
3. Configure DNS as instructed

### 5.2 Railway Custom Domain
1. In Railway dashboard, go to "Settings"
2. Add custom domain
3. Configure DNS

## Troubleshooting

### Common Issues:

1. **CORS Errors**: Make sure your Railway backend has CORS configured (already done in app.py)

2. **Build Failures**: 
   - Check Railway logs for Python version issues
   - Ensure all dependencies are in `requirements.txt`

3. **API Connection Issues**:
   - Verify the API URL in frontend/script.js
   - Check Railway app is running
   - Test health endpoint

4. **File Download Issues**:
   - Railway has ephemeral storage, files may not persist
   - Consider using cloud storage (AWS S3, etc.) for production

## Environment Variables Reference

### Railway (Backend)
```
PORT=5000
FLASK_ENV=production
```

### Netlify (Frontend)
```
REACT_APP_API_URL=https://your-railway-app-url.railway.app/api
```

## Cost Considerations

### Free Tiers:
- **Netlify**: 100GB bandwidth/month, unlimited sites
- **Railway**: $5 credit/month (usually enough for small apps)

### Scaling:
- Consider moving to paid plans for production use
- Implement rate limiting and file size restrictions
- Use cloud storage for downloaded files

## Security Notes

1. **Rate Limiting**: Implement rate limiting on your API endpoints
2. **File Cleanup**: Set up automatic cleanup of downloaded files
3. **CORS**: Configure CORS properly for production
4. **Environment Variables**: Never commit sensitive data to Git

## Next Steps

1. Set up monitoring and logging
2. Implement user authentication
3. Add file storage (AWS S3, Google Cloud Storage)
4. Set up CI/CD pipelines
5. Add error tracking (Sentry, etc.) 