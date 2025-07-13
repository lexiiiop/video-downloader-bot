# 🔧 GitHub Repository Setup

## Issue: Repository Not Found
The error `fatal: repository 'https://github.com/lexiiiop/video-downloader-bot.git/' not found` means the repository doesn't exist on GitHub yet.

## Solution: Create the Repository First

### Step 1: Create Repository on GitHub
1. Go to [GitHub.com](https://github.com)
2. Sign in to your account
3. Click the **"+"** icon in the top right
4. Select **"New repository"**
5. Fill in the details:
   - **Repository name**: `video-downloader-bot`
   - **Description**: `Video Downloader Bot with Netlify + Railway deployment`
   - **Visibility**: Public (or Private if you prefer)
   - **DO NOT** check "Add a README file" (we already have one)
   - **DO NOT** check "Add .gitignore" (we already have one)
6. Click **"Create repository"**

### Step 2: Connect Your Local Repository
After creating the repository, GitHub will show you commands. Use these:

```bash
# Remove the old remote (if any)
git remote remove origin

# Add the correct remote (replace YOUR_USERNAME with your actual GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/video-downloader-bot.git

# Push to GitHub
git push -u origin main
```

### Step 3: Verify the Push
You should see output like:
```
Enumerating objects: 25, done.
Counting objects: 100% (25/25), done.
Delta compression using up to 8 threads
Compressing objects: 100% (20/20), done.
Writing objects: 100% (25/25), done.
Total 25 (delta 0), reused 0 (delta 0), pack-reused 0
To https://github.com/YOUR_USERNAME/video-downloader-bot.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## Alternative: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Create repository using GitHub CLI
gh repo create video-downloader-bot --public --source=. --remote=origin --push
```

## After GitHub Setup

Once your repository is on GitHub, you can proceed with deployment:

1. **Deploy Backend to Railway:**
   - Go to [Railway.app](https://railway.app)
   - Connect your GitHub account
   - Create new project from your repository
   - Select the `backend` directory

2. **Deploy Frontend to Netlify:**
   - Go to [Netlify.com](https://netlify.com)
   - Connect your GitHub account
   - Create new site from your repository
   - Set publish directory to `frontend`

## Troubleshooting

### If you get authentication errors:
1. Use GitHub CLI: `gh auth login`
2. Or use SSH: `git remote set-url origin git@github.com:YOUR_USERNAME/video-downloader-bot.git`
3. Or use Personal Access Token

### If repository name is taken:
- Try a different name like `video-downloader-app` or `my-video-downloader`

### If you want to use a different GitHub account:
- Update the remote URL with the correct username
- Make sure you're logged into the right GitHub account

## Next Steps

After successfully pushing to GitHub:
1. Run `deploy.bat` (Windows) or `./deploy.sh` (Linux/Mac)
2. Follow the deployment instructions
3. Deploy to Railway and Netlify
4. Update API endpoints
5. Test your deployment

---

**Need help?** Check the main `deploy.md` file for detailed deployment instructions. 