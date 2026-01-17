/* Playback History Module */

(function() {
    'use strict';

    // API Endpoints
    const API_PLAYBACK_UPDATE = '/api/playback/update';
    const API_PLAYBACK_LIST = '/api/playback/list';
    const API_PLAYBACK_EPISODE = '/api/playback/episode';
    const API_PLAYBACK_LATEST = '/api/playback/latest';
    const API_PLAYBACK_BATCH = '/api/playback/batch';

    // Save interval (every 5 seconds)
    const SAVE_INTERVAL_MS = 5000;

    // State
    let saveTimer = null;
    let lastSavedPosition = 0;
    let currentAnimeData = null;

    // ============================================
    // Progress Tracking
    // ============================================

    function startProgressTracking(animeData, episodeIndex) {
        if (!animeData || !animeData.anime || !animeData.episodes) return;

        currentAnimeData = animeData;
        const episode = animeData.episodes[episodeIndex];
        if (!episode) return;

        // Clear any existing timer
        stopProgressTracking();

        // Start tracking with video element
        const video = document.getElementById('videoPlayer');
        if (video) {
            // Save immediately when starting
            saveProgress(animeData.anime, episode, video.currentTime);

            // Set up periodic saving
            saveTimer = setInterval(() => {
                if (!video.paused) {
                    const currentTime = video.currentTime;
                    // Only save if position changed significantly
                    if (Math.abs(currentTime - lastSavedPosition) > 2) {
                        saveProgress(animeData.anime, episode, currentTime);
                    }
                }
            }, SAVE_INTERVAL_MS);

            // Also save before page unload
            window.addEventListener('beforeunload', () => {
                if (video) {
                    saveProgress(animeData.anime, episode, video.currentTime);
                }
            });
        }
    }

    function stopProgressTracking() {
        if (saveTimer) {
            clearInterval(saveTimer);
            saveTimer = null;
        }
    }

    function saveProgress(anime, episode, position) {
        // Don't save if position is 0 or very small
        if (position < 1) return;

        lastSavedPosition = position;

        fetch(API_PLAYBACK_UPDATE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                anime_id: anime.id,
                anime_title: anime.title,
                episode_id: episode.id,
                episode_num: episode.episode,
                position_seconds: position,
                total_seconds: 0, // Could be set from video duration
                cover_url: anime.cover_url || ''
            })
        }).catch(error => {
            console.error('Failed to save playback progress:', error);
        });
    }

    // ============================================
    // Restore Playback
    // ============================================

    async function getEpisodeProgress(animeId, episodeId) {
        try {
            const response = await fetch(
                API_PLAYBACK_EPISODE + '?anime_id=' + animeId + '&episode_id=' + episodeId
            );
            const data = await response.json();
            return data.data;
        } catch (error) {
            console.error('Failed to get episode progress:', error);
            return null;
        }
    }

    async function restorePlaybackPosition(video, animeId, episodeId) {
        const progress = await getEpisodeProgress(animeId, episodeId);
        if (progress && progress.position_seconds > 5) {
            // Ask user if they want to resume
            const shouldResume = confirm(
                '上次播放到 ' + progress.position_formatted + '，是否继续？'
            );
            if (shouldResume) {
                video.currentTime = progress.position_seconds;
                return true;
            }
        }
        return false;
    }

    // ============================================
    // History List
    // ============================================

    async function fetchHistory(limit = 50) {
        try {
            const response = await fetch(API_PLAYBACK_LIST + '?limit=' + limit);
            const data = await response.json();
            return data.data || [];
        } catch (error) {
            console.error('Failed to fetch playback history:', error);
            return [];
        }
    }

    // ============================================
    // Episode Progress Indicators
    // ============================================

    async function fetchEpisodeProgressBatch(episodes, animeId) {
        if (!episodes || episodes.length === 0) return {};

        // Build IDs string
        const idPairs = episodes.map(ep => animeId + ':' + ep.id).join(',');

        try {
            const response = await fetch(API_PLAYBACK_BATCH + '?ids=' + encodeURIComponent(idPairs));
            const data = await response.json();
            return data.data || {};
        } catch (error) {
            console.error('Failed to fetch episode progress batch:', error);
            return {};
        }
    }

    function renderEpisodeWithProgress(episode, progress, isActive) {
        let progressHtml = '';
        if (progress) {
            const percent = progress.total_seconds > 0
                ? Math.min(100, Math.round((progress.position_seconds / progress.total_seconds) * 100))
                : 0;

            // Calculate color intensity based on progress
            const intensity = Math.max(0.1, Math.min(0.8, percent / 100));
            const color = `rgba(124, 92, 255, ${intensity + 0.1})`;
            const borderColor = percent >= 90 ? 'var(--accent-color)' : 'var(--border-color)';

            progressHtml = `
                <div class="episode-progress-bar" style="
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #ff6b9d, #7c5cff);
                    width: ${percent}%;
                    transition: width 0.3s ease;
                "></div>
                <div class="episode-progress-text" style="
                    font-size: 0.7rem;
                    color: var(--text-secondary);
                    margin-top: 4px;
                ">${progress.position_formatted}</div>
            `;

            return `
                <div class="episode-card ${isActive ? 'active' : ''}"
                     data-idx="${episode.idx}" style="position: relative; border-color: ${borderColor};">
                    <div class="episode-card-num">第${episode.episode}集</div>
                    <div class="episode-card-date">${episode.date}</div>
                    ${progressHtml}
                </div>
            `;
        }

        return `
            <div class="episode-card ${isActive ? 'active' : ''}" data-idx="${episode.idx}">
                <div class="episode-card-num">第${episode.episode}集</div>
                <div class="episode-card-date">${episode.date}</div>
            </div>
        `;
    }

    // ============================================
    // Public API
    // ============================================

    window.PlaybackHistory = {
        startTracking: startProgressTracking,
        stopTracking: stopProgressTracking,
        saveProgress: saveProgress,
        getProgress: getEpisodeProgress,
        restorePosition: restorePlaybackPosition,
        fetchHistory: fetchHistory,
        fetchBatchProgress: fetchEpisodeProgressBatch,
        renderWithProgress: renderEpisodeWithProgress
    };
})();
