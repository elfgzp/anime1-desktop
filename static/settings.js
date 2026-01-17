/* Settings Page JavaScript */

(function() {
    'use strict';

    const API_SETTINGS_THEME = '/api/settings/theme';
    const API_SETTINGS_ABOUT = '/api/settings/about';
    const API_SETTINGS_CHECK_UPDATE = '/api/settings/check_update';
    const API_SETTINGS_CACHE = '/api/settings/cache';
    const API_SETTINGS_CACHE_CLEAR = '/api/settings/cache/clear';
    const THEME_SYSTEM = 'system';
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';

    const elements = {
        themeSelect: document.getElementById('themeSelect'),
        checkUpdateBtn: document.getElementById('checkUpdateBtn'),
        aboutInfo: document.getElementById('aboutInfo'),
        // Cache elements
        cacheCoverCount: document.getElementById('cacheCoverCount'),
        cacheDbSize: document.getElementById('cacheDbSize'),
        cacheFavoriteCount: document.getElementById('cacheFavoriteCount'),
        clearCoverCacheBtn: document.getElementById('clearCoverCacheBtn'),
        clearAllCacheBtn: document.getElementById('clearAllCacheBtn')
    };

    // Load current theme
    async function loadTheme() {
        try {
            const response = await fetch(API_SETTINGS_THEME);
            const data = await response.json();

            if (data.success && data.data) {
                const theme = data.data.theme;
                elements.themeSelect.value = theme;
                applyTheme(theme);
            }
        } catch (error) {
            console.error('Error loading theme:', error);
        }
    }

    // Apply theme
    function applyTheme(theme) {
        const html = document.documentElement;
        html.classList.remove('theme-dark', 'theme-light');

        if (theme === THEME_SYSTEM) {
            // Detect system preference
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            html.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
        } else {
            html.classList.add('theme-' + theme);
        }
    }

    // Save theme
    async function saveTheme(theme) {
        try {
            const response = await fetch(API_SETTINGS_THEME, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ theme: theme })
            });

            const data = await response.json();
            if (data.success) {
                applyTheme(theme);
            }
        } catch (error) {
            console.error('Error saving theme:', error);
        }
    }

    // Load about info
    async function loadAbout() {
        try {
            const response = await fetch(API_SETTINGS_ABOUT);
            const data = await response.json();

            if (data.success && data.data) {
                const info = data.data;
                elements.aboutInfo.innerHTML =
                    '<p><strong>版本:</strong> ' + info.version + '</p>' +
                    '<p><strong>更新渠道:</strong> ' + info.channel + '</p>' +
                    '<p><strong>仓库地址:</strong> <a href="' + info.repository + '" target="_blank">' + info.repository + '</a></p>';
            }
        } catch (error) {
            console.error('Error loading about info:', error);
            elements.aboutInfo.innerHTML = '<p>加载失败</p>';
        }
    }

    // Load cache info
    async function loadCacheInfo() {
        try {
            const response = await fetch(API_SETTINGS_CACHE);
            const data = await response.json();

            if (data.success && data.data) {
                const info = data.data;
                if (elements.cacheCoverCount) {
                    elements.cacheCoverCount.textContent = info.cover_count;
                }
                if (elements.cacheDbSize) {
                    elements.cacheDbSize.textContent = info.database_size_formatted;
                }
                if (elements.cacheFavoriteCount) {
                    elements.cacheFavoriteCount.textContent = info.favorite_count;
                }
            }
        } catch (error) {
            console.error('Error loading cache info:', error);
        }
    }

    // Clear cache
    async function clearCache(type) {
        if (!confirm('确定要清理缓存吗？此操作不可撤销。')) {
            return;
        }

        try {
            const response = await fetch(API_SETTINGS_CACHE_CLEAR, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ type: type })
            });

            const data = await response.json();
            if (data.success) {
                alert(data.message);
                loadCacheInfo();
            } else {
                alert('清理失败');
            }
        } catch (error) {
            console.error('Error clearing cache:', error);
            alert('清理失败');
        }
    }

    // Check for updates
    async function checkUpdate() {
        try {
            elements.checkUpdateBtn.disabled = true;
            elements.checkUpdateBtn.textContent = '检查中...';

            const response = await fetch(API_SETTINGS_CHECK_UPDATE);
            const data = await response.json();

            if (data.has_update) {
                alert('发现新版本: ' + data.latest_version + '\n当前版本: ' + data.current_version);
            } else {
                alert('已是最新版本');
            }
        } catch (error) {
            console.error('Error checking update:', error);
            alert('检查更新失败');
        } finally {
            elements.checkUpdateBtn.disabled = false;
            elements.checkUpdateBtn.textContent = '检查更新';
        }
    }

    // Event listeners
    elements.themeSelect.addEventListener('change', function(e) {
        saveTheme(e.target.value);
    });

    elements.checkUpdateBtn.addEventListener('click', checkUpdate);

    if (elements.clearCoverCacheBtn) {
        elements.clearCoverCacheBtn.addEventListener('click', function() {
            clearCache('covers');
        });
    }

    if (elements.clearAllCacheBtn) {
        elements.clearAllCacheBtn.addEventListener('click', function() {
            clearCache('all');
        });
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
        if (elements.themeSelect.value === THEME_SYSTEM) {
            applyTheme(THEME_SYSTEM);
        }
    });

    // Initialize
    function init() {
        loadTheme();
        loadAbout();
        loadCacheInfo();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
