// LUMEN - Advanced Media Downloader
class LumenDownloader {
    constructor() {
        this.apiUrl = 'https://video-downloader-bot-production.up.railway.app/api';
        this.currentUrl = '';
        this.videoInfo = null;
        this.downloadId = null;
        this.progressInterval = null;
        
        this.initializeElements();
        this.bindEvents();
        this.setupAutoDetection();
    }

    initializeElements() {
        // Input elements
        this.urlInput = document.getElementById('urlInput');
        this.detectBtn = document.getElementById('detectBtn');
        
        // Platform detection
        this.platformInfo = document.getElementById('platformInfo');
        this.platformIcon = this.platformInfo.querySelector('.platform-icon');
        this.platformName = this.platformInfo.querySelector('.platform-name');
        
        // Sections
        this.downloadOptions = document.getElementById('downloadOptions');
        this.progressSection = document.getElementById('progressSection');
        this.resultSection = document.getElementById('resultSection');
        this.errorSection = document.getElementById('errorSection');
        
        // Progress elements
        this.progressFill = this.progressSection.querySelector('.progress-fill');
        this.progressText = this.progressSection.querySelector('.progress-text');
        this.progressStatus = this.progressSection.querySelector('.progress-status');
        
        // Result elements
        this.fileName = this.resultSection.querySelector('.file-name');
        this.fileSize = this.resultSection.querySelector('.file-size');
        this.downloadLink = document.getElementById('downloadLink');
        
        // Error elements
        this.errorMessage = this.errorSection.querySelector('.error-message');
    }

    bindEvents() {
        // URL input events
        this.urlInput.addEventListener('input', () => this.handleUrlInput());
        this.urlInput.addEventListener('paste', () => this.handleUrlPaste());
        
        // Detect button
        this.detectBtn.addEventListener('click', () => this.detectPlatform());
        
        // Download buttons
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDownload(e));
        });
    }

    setupAutoDetection() {
        // Auto-detect platform when URL is pasted
        this.urlInput.addEventListener('paste', () => {
            setTimeout(() => {
                if (this.isValidUrl(this.urlInput.value)) {
                    this.detectPlatform();
                }
            }, 100);
        });
    }

    handleUrlInput() {
        const url = this.urlInput.value.trim();
        this.detectBtn.disabled = !this.isValidUrl(url);
        
        if (!url) {
            this.hideAllSections();
        }
    }

    handleUrlPaste() {
        // Auto-detect when URL is pasted
        setTimeout(() => {
            if (this.isValidUrl(this.urlInput.value)) {
                this.detectPlatform();
            }
        }, 100);
    }

    isValidUrl(url) {
        if (!url) return false;
        
        // Check for common video platform URLs
        const platforms = [
            'youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com',
            'facebook.com', 'twitter.com', 'x.com', 'vimeo.com',
            'dailymotion.com', 'reddit.com', 'twitch.tv'
        ];
        
        return platforms.some(platform => url.includes(platform));
    }

    detectPlatform() {
        const url = this.urlInput.value.trim();
        if (!this.isValidUrl(url)) {
            this.showError('Please enter a valid video URL from a supported platform.');
            return;
        }

        this.currentUrl = url;
        const platform = this.getPlatformFromUrl(url);
        
        // Show platform detection
        this.showPlatformInfo(platform);
        
        // Get video info
        this.getVideoInfo(url);
    }

    getPlatformFromUrl(url) {
        const urlLower = url.toLowerCase();
        
        if (urlLower.includes('youtube.com') || urlLower.includes('youtu.be')) {
            return {
                name: 'YouTube',
                icon: 'smart_display',
                color: '#ff0000'
            };
        } else if (urlLower.includes('instagram.com')) {
            return {
                name: 'Instagram',
                icon: 'camera_alt',
                color: '#e4405f'
            };
        } else if (urlLower.includes('tiktok.com')) {
            return {
                name: 'TikTok',
                icon: 'music_note',
                color: '#000000'
            };
        } else if (urlLower.includes('facebook.com')) {
            return {
                name: 'Facebook',
                icon: 'facebook',
                color: '#1877f2'
            };
        } else if (urlLower.includes('twitter.com') || urlLower.includes('x.com')) {
            return {
                name: 'X (Twitter)',
                icon: 'flutter_dash',
                color: '#1da1f2'
            };
        } else if (urlLower.includes('vimeo.com')) {
            return {
                name: 'Vimeo',
                icon: 'play_circle',
                color: '#1ab7ea'
            };
        } else if (urlLower.includes('dailymotion.com')) {
            return {
                name: 'Dailymotion',
                icon: 'video_library',
                color: '#0066dc'
            };
        } else if (urlLower.includes('reddit.com')) {
            return {
                name: 'Reddit',
                icon: 'forum',
                color: '#ff4500'
            };
        } else if (urlLower.includes('twitch.tv')) {
            return {
                name: 'Twitch',
                icon: 'live_tv',
                color: '#9146ff'
            };
        }
        
        return {
            name: 'Unknown Platform',
            icon: 'link',
            color: '#666666'
        };
    }

    showPlatformInfo(platform) {
        this.platformIcon.textContent = platform.icon;
        this.platformName.textContent = platform.name;
        this.platformInfo.classList.remove('hidden');
        
        // Add color to platform icon
        this.platformIcon.style.color = platform.color;
    }

    async getVideoInfo(url) {
        try {
            this.showProgress('Analyzing video...', 10);
            
            const response = await fetch(`${this.apiUrl}/info`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.videoInfo = data;
            this.showProgress('Video analyzed successfully!', 100);
            
            // Show download options after a brief delay
            setTimeout(() => {
                this.showDownloadOptions();
            }, 500);

        } catch (error) {
            console.error('Error getting video info:', error);
            this.showError(`Failed to analyze video: ${error.message}`);
        }
    }

    async handleDownload(event) {
        const format = event.currentTarget.dataset.format;
        const button = event.currentTarget;
        
        // Disable all download buttons
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.5';
        });
        
        try {
            await this.startDownload(format);
        } catch (error) {
            console.error('Download error:', error);
            this.showError(`Download failed: ${error.message}`);
            
            // Re-enable buttons
            document.querySelectorAll('.download-btn').forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '1';
            });
        }
    }

    async startDownload(format) {
        try {
            this.showProgress('Initializing download...', 5);
            
            const response = await fetch(`${this.apiUrl}/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: this.currentUrl,
                    format: format,
                    title: this.videoInfo?.title || 'video'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.downloadId = data.download_id;
            this.showProgress('Download started...', 10);
            
            // Start progress tracking
            this.trackProgress();

        } catch (error) {
            throw new Error(`Failed to start download: ${error.message}`);
        }
    }

    async trackProgress() {
        if (!this.downloadId) return;

        this.progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiUrl}/progress/${this.downloadId}`);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }

                const progress = data.progress || 0;
                const status = data.status || 'Downloading...';
                
                this.updateProgress(progress, status);

                if (data.completed) {
                    clearInterval(this.progressInterval);
                    this.handleDownloadComplete(data);
                }

            } catch (error) {
                console.error('Progress tracking error:', error);
                clearInterval(this.progressInterval);
                this.showError(`Progress tracking failed: ${error.message}`);
            }
        }, 1000);
    }

    updateProgress(percentage, status) {
        this.progressFill.style.width = `${percentage}%`;
        this.progressText.textContent = `${Math.round(percentage)}%`;
        this.progressStatus.textContent = status;
    }

    handleDownloadComplete(data) {
        this.showProgress('Download completed!', 100);
        
        setTimeout(() => {
            this.showResult(data);
        }, 500);
    }

    showProgress(status, percentage = 0) {
        this.hideAllSections();
        this.progressSection.classList.remove('hidden');
        this.updateProgress(percentage, status);
    }

    showDownloadOptions() {
        this.hideAllSections();
        this.downloadOptions.classList.remove('hidden');
        
        // Re-enable download buttons
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
        });
    }

    showResult(data) {
        this.hideAllSections();
        this.resultSection.classList.remove('hidden');
        
        // Set file information
        this.fileName.textContent = data.filename || 'Downloaded File';
        this.fileSize.textContent = data.file_size ? `Size: ${this.formatFileSize(data.file_size)}` : '';
        
        // Set download link using the stored download ID
        this.downloadLink.href = `${this.apiUrl}/file/${this.downloadId}`;
        this.downloadLink.download = data.filename || 'video.mp4';
        
        // Auto-download after 2 seconds
        setTimeout(() => {
            this.downloadLink.click();
        }, 2000);
    }

    showError(message) {
        this.hideAllSections();
        this.errorSection.classList.remove('hidden');
        this.errorMessage.textContent = message;
    }

    hideAllSections() {
        this.downloadOptions.classList.add('hidden');
        this.progressSection.classList.add('hidden');
        this.resultSection.classList.add('hidden');
        this.errorSection.classList.add('hidden');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    resetUI() {
        this.hideAllSections();
        this.platformInfo.classList.add('hidden');
        this.urlInput.value = '';
        this.detectBtn.disabled = true;
        this.currentUrl = '';
        this.videoInfo = null;
        this.downloadId = null;
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
        
        // Re-enable all buttons
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
        });
    }
}

// Global function for retry button
function resetUI() {
    if (window.lumenDownloader) {
        window.lumenDownloader.resetUI();
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    window.lumenDownloader = new LumenDownloader();
    
    // Add some nice loading animations
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease-in-out';
        document.body.style.opacity = '1';
    }, 100);
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
            case 'v':
                // Auto-detect on paste
                setTimeout(() => {
                    if (window.lumenDownloader && window.lumenDownloader.isValidUrl(window.lumenDownloader.urlInput.value)) {
                        window.lumenDownloader.detectPlatform();
                    }
                }, 100);
                break;
            case 'r':
                // Reset UI
                e.preventDefault();
                resetUI();
                break;
        }
    }
    
    // Enter key to detect platform
    if (e.key === 'Enter' && document.activeElement === window.lumenDownloader?.urlInput) {
        if (window.lumenDownloader && window.lumenDownloader.isValidUrl(window.lumenDownloader.urlInput.value)) {
            window.lumenDownloader.detectPlatform();
        }
    }
}); 