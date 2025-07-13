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
        this.setupCustomCursor();
    }

    initializeElements() {
        // Input elements
        this.urlInput = document.getElementById('urlInput');
        this.detectBtn = document.getElementById('detectBtn');
        
        // Platform detection
        this.platformInfo = document.getElementById('platformInfo');
        this.platformIcon = this.platformInfo.querySelector('.platform-icon');
        this.platformName = this.platformInfo.querySelector('.platform-name');
        
        // Video preview
        this.videoPreview = document.getElementById('videoPreview');
        this.videoThumbnail = document.getElementById('videoThumbnail');
        this.videoTitle = document.getElementById('videoTitle');
        
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
        
        // Quality selectors
        this.videoQualitySelect = document.getElementById('videoQualitySelect');
        this.audioQualitySelect = document.getElementById('audioQualitySelect');
        this.videoOnlyQualitySelect = document.getElementById('videoOnlyQualitySelect');
    }

    setupCustomCursor() {
        // Create custom cursor element
        const cursor = document.createElement('div');
        cursor.className = 'custom-cursor';
        document.body.appendChild(cursor);

        // Track mouse movement
        document.addEventListener('mousemove', (e) => {
            cursor.style.left = e.clientX + 'px';
            cursor.style.top = e.clientY + 'px';
        });

        // Add hover effect for interactive elements
        const interactiveElements = document.querySelectorAll('button, input, select, a, .option-card');
        interactiveElements.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.classList.add('hover');
            });
            el.addEventListener('mouseleave', () => {
                cursor.classList.remove('hover');
            });
        });
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
        
        // Quality selector events
        this.videoQualitySelect.addEventListener('change', () => this.handleQualityChange('video'));
        this.audioQualitySelect.addEventListener('change', () => this.handleQualityChange('audio'));
        this.videoOnlyQualitySelect.addEventListener('change', () => this.handleQualityChange('video_only'));
    }

    handleQualityChange(format) {
        const select = this[`${format}QualitySelect`];
        const button = select.closest('.option-card').querySelector('.download-btn');
        
        if (select.value) {
            button.disabled = false;
        } else {
            button.disabled = true;
        }
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
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.videoInfo = data;
            this.showVideoPreview(data);
            this.populateQualityOptions(data);
            this.showDownloadOptions();
            
        } catch (error) {
            console.error('Error getting video info:', error);
            this.showError(`Failed to analyze video: ${error.message}`);
        }
    }

    showVideoPreview(info) {
        if (info.thumbnail) {
            this.videoThumbnail.src = info.thumbnail;
            this.videoThumbnail.style.display = 'block';
        } else {
            this.videoThumbnail.style.display = 'none';
        }
        
        this.videoTitle.textContent = info.title || 'Unknown Title';
        this.videoPreview.classList.remove('hidden');
    }

    populateQualityOptions(info) {
        const formats = info.formats || [];
        
        // Clear existing options
        this.videoQualitySelect.innerHTML = '<option value="">Select quality...</option>';
        this.audioQualitySelect.innerHTML = '<option value="">Select quality...</option>';
        this.videoOnlyQualitySelect.innerHTML = '<option value="">Select quality...</option>';
        
        // Populate video formats (with audio)
        const videoFormats = formats.filter(fmt => 
            fmt.has_audio && fmt.ext && ['mp4', 'webm', 'mkv'].includes(fmt.ext)
        );
        videoFormats.forEach(fmt => {
            const option = document.createElement('option');
            option.value = fmt.format_id;
            option.textContent = `${fmt.height}p ${fmt.ext.toUpperCase()} (${this.formatFileSize(fmt.filesize)})`;
            this.videoQualitySelect.appendChild(option);
        });
        
        // Populate audio formats
        const audioFormats = formats.filter(fmt => 
            fmt.acodec && fmt.acodec !== 'none' && !fmt.vcodec
        );
        audioFormats.forEach(fmt => {
            const option = document.createElement('option');
            option.value = fmt.format_id;
            option.textContent = `${fmt.ext.toUpperCase()} Audio (${this.formatFileSize(fmt.filesize)})`;
            this.audioQualitySelect.appendChild(option);
        });
        
        // Populate video-only formats
        const videoOnlyFormats = formats.filter(fmt => 
            fmt.vcodec && fmt.vcodec !== 'none' && (!fmt.acodec || fmt.acodec === 'none')
        );
        videoOnlyFormats.forEach(fmt => {
            const option = document.createElement('option');
            option.value = fmt.format_id;
            option.textContent = `${fmt.height}p ${fmt.ext.toUpperCase()} Video Only (${this.formatFileSize(fmt.filesize)})`;
            this.videoOnlyQualitySelect.appendChild(option);
        });
    }

    async handleDownload(event) {
        const button = event.currentTarget;
        const format = button.dataset.format;
        
        if (format === 'best') {
            await this.startDownload('best');
        } else {
            const select = this[`${format}QualitySelect`];
            if (select.value) {
                await this.startDownload(select.value);
            } else {
                this.showError('Please select a quality option first.');
            }
        }
    }

    async startDownload(format) {
        try {
            this.showProgress('Starting download...', 0);
            
            const response = await fetch(`${this.apiUrl}/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: this.currentUrl,
                    format: format,
                    title: this.videoInfo.title
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
            this.trackProgress();
            
        } catch (error) {
            console.error('Error starting download:', error);
            this.showError(`Failed to start download: ${error.message}`);
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

                if (data.status === 'completed') {
                    clearInterval(this.progressInterval);
                    this.handleDownloadComplete(data);
                } else if (data.status === 'error') {
                    clearInterval(this.progressInterval);
                    this.showError(data.error || 'Download failed');
                } else {
                    this.updateProgress(data.progress || 0, data.status || 'downloading');
                }
                
            } catch (error) {
                console.error('Error tracking progress:', error);
                clearInterval(this.progressInterval);
                this.showError(`Progress tracking failed: ${error.message}`);
            }
        }, 1000);
    }

    updateProgress(percentage, status) {
        this.progressFill.style.width = `${percentage}%`;
        this.progressText.textContent = `${percentage}%`;
        this.progressStatus.textContent = status === 'downloading' ? 'Downloading...' : status;
    }

    handleDownloadComplete(data) {
        this.showResult(data);
    }

    showProgress(status, percentage = 0) {
        this.hideAllSections();
        this.progressSection.classList.remove('hidden');
        this.updateProgress(percentage, status);
    }

    showDownloadOptions() {
        this.downloadOptions.classList.remove('hidden');
    }

    showResult(data) {
        this.hideAllSections();
        this.resultSection.classList.remove('hidden');
        
        // Set download link
        this.downloadLink.href = `${this.apiUrl}/file/${this.downloadId}`;
        
        // Set file info
        this.fileName.textContent = this.videoInfo.title || 'Downloaded File';
        this.fileSize.textContent = data.filesize ? this.formatFileSize(data.filesize) : 'Unknown size';
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
        this.videoPreview.classList.add('hidden');
    }

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return 'Unknown size';
        
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    resetUI() {
        this.hideAllSections();
        this.urlInput.value = '';
        this.detectBtn.disabled = true;
        this.currentUrl = '';
        this.videoInfo = null;
        this.downloadId = null;
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new LumenDownloader();
});

// Global reset function
function resetUI() {
    if (window.lumenDownloader) {
        window.lumenDownloader.resetUI();
    }
} 