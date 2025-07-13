#!/bin/bash

echo "🚀 Video Downloader Bot - Deployment Script"
echo "=========================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for deployment"
    echo "✅ Git repository initialized"
else
    echo "📁 Git repository already exists"
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. 🚂 Deploy Backend to Railway:"
echo "   - Go to https://railway.app"
echo "   - Sign in with GitHub"
echo "   - Create new project from GitHub repo"
echo "   - Select 'backend' directory"
echo "   - Add environment variables:"
echo "     PORT=5000"
echo "     FLASK_ENV=production"
echo ""
echo "2. 🌐 Deploy Frontend to Netlify:"
echo "   - Go to https://netlify.com"
echo "   - Sign in with GitHub"
echo "   - Create new site from Git"
echo "   - Select your repository"
echo "   - Set publish directory to 'frontend'"
echo ""
echo "3. 🔗 Update API Endpoint:"
echo "   After Railway deployment, run:"
echo "   node update-api-url.js https://your-railway-app.railway.app"
echo ""
echo "4. 🎉 Test Your Deployment:"
echo "   - Test backend: https://your-railway-app.railway.app/api/health"
echo "   - Test frontend: Your Netlify URL"
echo ""
echo "📖 For detailed instructions, see deploy.md"
echo ""
echo "Happy deploying! 🎊" 