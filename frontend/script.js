class VideoDownloader {
    constructor() {
        this.apiBase = 'https://video-downloader-bot-production.up.railway.app/api';
        this.currentVideoInfo = null;
        this.selectedFormat = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.hideAllSections();
    }

    bindEvents() {
        const analyzeBtn = document.getElementById('analyzeBtn');
        const videoUrlInput = document.getElementById('videoUrl');
        const downloadFileBtn = document.getElementById('downloadFileBtn');

        analyzeBtn.addEventListener('click', () => this.analyzeVideo());
        videoUrlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.analyzeVideo();
            }
        });

        downloadFileBtn.addEventListener('click', () => this.downloadFile());
    }

    hideAllSections() {
        const sections = [
            'loadingSection',
            'errorSection', 
            'videoInfoSection',
            'downloadSection',
            'successSection'
        ];
        
        sections.forEach(section => {
            document.getElementById(section).classList.add('hidden');
        });
    }

    showSection(sectionId) {
        this.hideAllSections();
        document.getElementById(sectionId).classList.remove('hidden');
    }

    async analyzeVideo() {
        const url = document.getElementById('videoUrl').value.trim();
        
        if (!url) {
            this.showError('Please enter a valid video URL');
            return;
        }

        if (!this.isValidUrl(url)) {
            this.showError('Please enter a valid URL');
            return;
        }

        this.showSection('loadingSection');

        try {
            const response = await fetch(`${this.apiBase}/info`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to analyze video');
            }

            this.currentVideoInfo = data;
            this.displayVideoInfo(data);
            this.showSection('videoInfoSection');

        } catch (error) {
            console.error('Error analyzing video:', error);
            this.showError(error.message || 'Failed to analyze video. Please check the URL and try again.');
        }
    }

    isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    displayVideoInfo(videoInfo) {
        // Display video thumbnail and details
        const thumbnail = document.getElementById('videoThumbnail');
        const title = document.getElementById('videoTitle');
        const duration = document.getElementById('videoDuration');

        thumbnail.src = videoInfo.thumbnail || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEyMCIgdmlld0JveD0iMCAwIDIwMCAxMjAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMTIwIiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik04MCA2MEwxMjAgODBMODAgMTAwVjYwWiIgZmlsbD0iIzk5OTk5OSIvPgo8L3N2Zz4K';
        title.textContent = videoInfo.title;
        duration.textContent = this.formatDuration(videoInfo.duration);

        // Display available formats
        this.displayFormats(videoInfo.formats);
    }

    formatDuration(seconds) {
        if (!seconds) return 'Unknown duration';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }

    displayFormats(formats) {
        const formatsList = document.getElementById('formatsList');
        formatsList.innerHTML = '';

        if (!formats || formats.length === 0) {
            formatsList.innerHTML = '<p>No downloadable formats found</p>';
            return;
        }

        // Sort formats by quality (height) and file size
        const sortedFormats = formats.sort((a, b) => {
            if (a.height !== b.height) {
                return b.height - a.height; // Higher resolution first
            }
            return a.filesize - b.filesize; // Smaller file size first
        });

        sortedFormats.forEach(format => {
            const formatCard = this.createFormatCard(format);
            formatsList.appendChild(formatCard);
        });
    }

    createFormatCard(format) {
        const card = document.createElement('div');
        card.className = 'format-card';
        card.dataset.formatId = format.format_id;

        const quality = format.height ? `${format.height}p` : format.format_note || 'Unknown';
        const size = format.filesize ? this.formatFileSize(format.filesize) : 'Unknown size';
        const extension = format.ext ? format.ext.toUpperCase() : 'Unknown';
        const hasAudio = format.has_audio ? '🎵' : '🔇';

        card.innerHTML = `
            <div class="format-header">
                <span class="format-quality">${quality}</span>
                <span class="format-size">${size}</span>
            </div>
            <div class="format-details">
                <span>Format: ${extension}</span>
                ${format.width ? `<span>Resolution: ${format.width}x${format.height}</span>` : ''}
                <span>Audio: ${hasAudio}</span>
            </div>
            <button class="download-btn" onclick="videoDownloader.downloadVideo('${format.format_id}')">
                <i class="fas fa-download"></i>
                Download ${extension}
            </button>
        `;

        return card;
    }

    formatFileSize(bytes) {
        if (!bytes) return 'Unknown size';
        
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(1024));
        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    }

    async downloadVideo(formatId) {
        if (!this.currentVideoInfo) {
            this.showError('No video information available');
            return;
        }

        this.selectedFormat = formatId;
        this.showSection('downloadSection');
        this.updateProgress(0, 'Starting download...');

        try {
            const response = await fetch(`${this.apiBase}/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: document.getElementById('videoUrl').value,
                    format_id: formatId
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Download failed');
            }

            this.updateProgress(100, 'Download completed!');
            
            // Store download info for file download
            this.downloadInfo = data;
            
            setTimeout(() => {
                this.showDownloadSuccess(data);
            }, 1000);

        } catch (error) {
            console.error('Error downloading video:', error);
            this.showError(error.message || 'Download failed. Please try again.');
        }
    }

    updateProgress(percentage, status) {
        const progressFill = document.getElementById('progressFill');
        const downloadStatus = document.getElementById('downloadStatus');

        progressFill.style.width = `${percentage}%`;
        downloadStatus.textContent = status;
    }

    showDownloadSuccess(downloadInfo) {
        const downloadInfoText = document.getElementById('downloadInfo');
        downloadInfoText.textContent = `File: ${downloadInfo.file_name} (${this.formatFileSize(downloadInfo.file_size)})`;
        
        this.showSection('successSection');
    }

    downloadFile() {
        if (!this.downloadInfo) {
            this.showError('No file available for download');
            return;
        }

        // Create a temporary link to trigger the download
        const link = document.createElement('a');
        link.href = `${this.apiBase}/download-file/${this.downloadInfo.file_name}`;
        link.download = this.downloadInfo.file_name;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.textContent = message;
        this.showSection('errorSection');
    }
}

// Initialize the application when the page loads
let videoDownloader;
document.addEventListener('DOMContentLoaded', () => {
    videoDownloader = new VideoDownloader();
});

// Global function for format card click handlers
window.videoDownloader = null;
document.addEventListener('DOMContentLoaded', () => {
    window.videoDownloader = videoDownloader;
}); 