/* Anime1 - Main JavaScript */

(function() {
    'use strict';

    // ============================================
    // Constants
    // ============================================

    // API Endpoints
    const API_ANIME = '/api/anime';
    const API_ANIME_SEARCH = '/api/anime/search';
    const API_COVERS = '/api/anime/covers';
    const API_UPDATE_CHECK = '/api/update/check';
    const API_UPDATE_INFO = '/api/update/info';
    const API_FAVORITE_ADD = '/api/favorite/add';
    const API_FAVORITE_REMOVE = '/api/favorite/remove';
    const API_FAVORITE_LIST = '/api/favorite/list';
    const API_FAVORITE_CHECK = '/api/favorite/check';
    const API_FAVORITE_IS_FAVORITE = '/api/favorite/is_favorite';
    const API_SETTINGS_THEME = '/api/settings/theme';

    // Adult content detection
    const ADULT_MARKER = '🔞';
    const ADULT_SITE_DOMAIN = 'anime1.pw';

    // CSS Classes
    const CLS_HIDDEN = 'hidden';
    const CLS_ACTIVE = 'active';

    // DOM IDs
    const ID_ANIME_GRID = 'animeGrid';
    const ID_EMPTY_STATE = 'emptyState';
    const ID_CURRENT_PAGE = 'currentPage';
    const ID_TOTAL_PAGES = 'totalPages';
    const ID_PREV_BTN = 'prevBtn';
    const ID_NEXT_BTN = 'nextBtn';
    const ID_JUMP_PAGE = 'jumpPage';
    const ID_JUMP_BTN = 'jumpBtn';
    const ID_CONTENT = 'content';
    const ID_PREVIEW_OVERLAY = 'previewOverlay';
    const ID_PREVIEW_IMAGE = 'previewImage';
    const ID_SEARCH_INPUT = 'searchInput';
    const ID_SEARCH_BTN = 'searchBtn';
    const ID_CLEAR_SEARCH_BTN = 'clearSearchBtn';
    const ID_SEARCH_OVERLAY = 'searchOverlay';
    const ID_LOADING_OVERLAY = 'loadingOverlay';
    const ID_CHECK_UPDATE_BTN = 'checkUpdateBtn';
    const ID_UPDATE_MODAL = 'updateModal';
    const ID_HEADER_COMPACT = 'headerCompact';
    const ID_UPDATE_BADGE = 'updateBadge';
    const ID_CLOSE_UPDATE_MODAL = 'closeUpdateModal';
    const ID_CURRENT_VERSION_TEXT = 'currentVersionText';
    const ID_LATEST_VERSION_TEXT = 'latestVersionText';
    const ID_PRERELEASE_BADGE = 'prereleaseBadge';
    const ID_RELEASE_NOTES = 'releaseNotes';
    const ID_DOWNLOAD_UPDATE_BTN = 'downloadUpdateBtn';
    const ID_CANCEL_UPDATE_BTN = 'cancelUpdateBtn';

    // UI Text
    const TEXT_PAGE_PREFIX = '第 ';
    const TEXT_PAGE_SUFFIX = ' 页';
    const TEXT_LOADING_FAILED = '获取失败:';
    const TEXT_IMAGE_FAILED = '加载图片失败';
    const TEXT_DEFAULT_VALUE = '-';
    const TEXT_COVER_IMG_ERROR = "this.style.display='none'";

    // Styles
    const FONT_SIZE_ADULT = 28;
    const FONT_SIZE_LOADING = 20;

    // Numbers
    const INITIAL_PAGE = 1;
    const FIRST_PAGE = 1;

    // ============================================
    // State management
    // ============================================

    const state = {
        page: INITIAL_PAGE,
        totalPages: INITIAL_PAGE,
        animeList: [],
        isLoading: false,
        isSearching: false,
        searchKeyword: ''
    };

    // DOM Elements
    const elements = {
        grid: document.getElementById(ID_ANIME_GRID),
        emptyState: document.getElementById(ID_EMPTY_STATE),
        currentPage: document.getElementById(ID_CURRENT_PAGE),
        totalPages: document.getElementById(ID_TOTAL_PAGES),
        prevBtn: document.getElementById(ID_PREV_BTN),
        nextBtn: document.getElementById(ID_NEXT_BTN),
        jumpPage: document.getElementById(ID_JUMP_PAGE),
        jumpBtn: document.getElementById(ID_JUMP_BTN),
        content: document.getElementById(ID_CONTENT),
        previewOverlay: document.getElementById(ID_PREVIEW_OVERLAY),
        previewImage: document.getElementById(ID_PREVIEW_IMAGE),
        searchInput: document.getElementById(ID_SEARCH_INPUT),
        searchBtn: document.getElementById(ID_SEARCH_BTN),
        clearSearchBtn: document.getElementById(ID_CLEAR_SEARCH_BTN),
        searchOverlay: document.getElementById(ID_SEARCH_OVERLAY),
        loadingOverlay: document.getElementById(ID_LOADING_OVERLAY),
        checkUpdateBtn: document.getElementById(ID_CHECK_UPDATE_BTN),
        headerCompact: document.getElementById(ID_HEADER_COMPACT),
        updateBadge: document.getElementById(ID_UPDATE_BADGE),
        updateModal: document.getElementById(ID_UPDATE_MODAL),
        closeUpdateModal: document.getElementById(ID_CLOSE_UPDATE_MODAL),
        currentVersionText: document.getElementById(ID_CURRENT_VERSION_TEXT),
        latestVersionText: document.getElementById(ID_LATEST_VERSION_TEXT),
        prereleaseBadge: document.getElementById(ID_PRERELEASE_BADGE),
        releaseNotes: document.getElementById(ID_RELEASE_NOTES),
        downloadUpdateBtn: document.getElementById(ID_DOWNLOAD_UPDATE_BTN),
        cancelUpdateBtn: document.getElementById(ID_CANCEL_UPDATE_BTN)
    };

    // ============================================
    // UI Functions
    // ============================================

    function showEmpty() {
        elements.content.classList.add(CLS_HIDDEN);
        elements.emptyState.classList.remove(CLS_HIDDEN);
    }

    function updatePagination() {
        elements.currentPage.textContent = state.page;
        elements.totalPages.textContent = state.totalPages;
        elements.prevBtn.disabled = state.page <= FIRST_PAGE;
        elements.nextBtn.disabled = state.page >= state.totalPages;
    }

    function openPreview(imageSrc) {
        elements.previewImage.src = imageSrc;
        elements.previewOverlay.classList.add(CLS_ACTIVE);
    }

    function closePreview() {
        elements.previewOverlay.classList.remove(CLS_ACTIVE);
    }

    // ============================================
    // API Functions
    // ============================================

    async function fetchAnimeList(page) {
        if (state.isLoading) return;

        state.isLoading = true;
        
        // 显示加载遮罩（仅在非搜索模式下显示，搜索模式使用 searchOverlay）
        if (!state.isSearching && elements.loadingOverlay) {
            elements.loadingOverlay.classList.remove(CLS_HIDDEN);
        }

        try {
            let url;
            if (state.isSearching && state.searchKeyword) {
                url = API_ANIME_SEARCH + '?q=' + encodeURIComponent(state.searchKeyword) + '&page=' + page;
            } else {
                url = API_ANIME + '?page=' + page;
            }

            const response = await fetch(url);
            const data = await response.json();

            state.page = data.current_page;
            state.totalPages = data.total_pages || Math.ceil(data.anime_list.length / 20);
            state.animeList = data.anime_list;

            // Render basic info first
            renderGrid(data.anime_list);
            updatePagination();

            // Parallel fetch covers (过滤掉18x番剧) - 不等待，直接异步加载
            if (data.anime_list.length > 0) {
                fetchCoversParallel(data.anime_list);
            }
        } catch (error) {
            console.error(TEXT_LOADING_FAILED, error);
            showEmpty();
            // 出错时也隐藏加载遮罩
            if (elements.loadingOverlay) {
                elements.loadingOverlay.classList.add(CLS_HIDDEN);
            }
        } finally {
            state.isLoading = false;
        }
    }

    async function searchAnime(keyword) {
        if (state.isLoading) return;

        state.isSearching = true;
        state.searchKeyword = keyword;
        state.page = INITIAL_PAGE;

        // Show search overlay
        elements.searchOverlay.classList.remove(CLS_HIDDEN);

        // Show/hide clear button
        elements.clearSearchBtn.classList.toggle(CLS_HIDDEN, !keyword);

        await fetchAnimeList(INITIAL_PAGE);

        // Hide search overlay after results are ready (covers may still be loading)
        elements.searchOverlay.classList.add(CLS_HIDDEN);
    }

    function clearSearch() {
        state.isSearching = false;
        state.searchKeyword = '';
        elements.searchInput.value = '';
        elements.clearSearchBtn.classList.add(CLS_HIDDEN);
        fetchAnimeList(INITIAL_PAGE);
    }

    function fetchCoversParallel(animeList) {
        // 过滤掉18x番剧（标题包含🔞或链接到 anime1.pw）
        const normalAnime = animeList.filter(anime =>
            !anime.title.includes(ADULT_MARKER) && !anime.detail_url.includes(ADULT_SITE_DOMAIN)
        );

        // 为每个动漫创建独立的请求，不等待顺序，直接处理返回结果
        normalAnime.forEach(anime => {
            fetch(API_COVERS + '?ids=' + anime.id)
                .then(res => res.json())
                .then(data => {
                    const result = data[0] || null;
                    if (result && result.cover_url) {
                        updateAnimeRow(anime.id, result);
                    }
                })
                .catch(() => {
                    // 静默失败，不显示错误
                });
        });
    }

    function updateAnimeRow(animeId, animeData) {
        const cardId = 'anime-card-' + animeId;
        const card = document.getElementById(cardId);
        if (!card) return;

        // Update cover image
        const coverCell = card.querySelector('.card-cover');
        coverCell.innerHTML = '<img src="' + animeData.cover_url + '" alt="' + animeData.title + '" onerror=' + TEXT_COVER_IMG_ERROR + '>';

        // Update other fields
        const metaCell = card.querySelector('.card-meta');
        if (metaCell) {
            metaCell.innerHTML =
                '<span class="tag tag-episode">第' + animeData.episode + '集</span>' +
                '<span class="tag tag-year">' + (animeData.year || TEXT_DEFAULT_VALUE) + '</span>' +
                '<span class="tag tag-season">' + (animeData.season || TEXT_DEFAULT_VALUE) + '</span>' +
                '<span class="tag tag-subtitle">' + (animeData.subtitle_group || TEXT_DEFAULT_VALUE) + '</span>';
        }

        card.classList.remove('card-loading');
    }

    // ============================================
    // Render Functions
    // ============================================

    function renderGrid(animeList) {
        if (!animeList || animeList.length === 0) {
            showEmpty();
            // 没有数据时隐藏加载遮罩
            if (elements.loadingOverlay) {
                elements.loadingOverlay.classList.add(CLS_HIDDEN);
            }
            return;
        }

        elements.content.classList.remove(CLS_HIDDEN);
        elements.emptyState.classList.add(CLS_HIDDEN);
        
        // 有数据时隐藏加载遮罩
        if (elements.loadingOverlay) {
            elements.loadingOverlay.classList.add(CLS_HIDDEN);
        }

        elements.grid.innerHTML = animeList.map(anime => {
            // 成人番剧：标题包含🔞或者链接到 anime1.pw
            const isAdult = anime.title.includes(ADULT_MARKER) || anime.detail_url.includes(ADULT_SITE_DOMAIN);
            const animeId = anime.id;
            const yearValue = anime.year || TEXT_DEFAULT_VALUE;
            const seasonValue = anime.season || TEXT_DEFAULT_VALUE;
            const subtitleValue = anime.subtitle_group || TEXT_DEFAULT_VALUE;

            let coverHtml;
            if (isAdult) {
                coverHtml = '<div class="adult-mark">' + ADULT_MARKER + '</div>';
            } else {
                coverHtml = '';
            }

            return '<div id="anime-card-wrapper-' + animeId + '" class="anime-card-wrapper">' +
                '<a id="anime-card-' + animeId + '" class="anime-card' + (isAdult ? '' : ' card-loading') + '" href="/anime/' + animeId + '">' +
                '<div class="card-cover">' + coverHtml + '</div>' +
                '<div class="card-content">' +
                '<div class="card-title">' + anime.title + '</div>' +
                '<div class="card-meta">' +
                '<span class="tag tag-episode">第' + anime.episode + '集</span>' +
                '<span class="tag tag-year">' + yearValue + '</span>' +
                '<span class="tag tag-season">' + seasonValue + '</span>' +
                '<span class="tag tag-subtitle">' + subtitleValue + '</span>' +
                '</div>' +
                '</div>' +
                '</a>' +
                '<button class="favorite-btn" data-anime-id="' + animeId + '" title="追番">⭐</button>' +
                '</div>';
        }).join('');
        
        // Bind favorite button events after rendering
        bindFavoriteButtons();
    }

    // ============================================
    // Event Handlers
    // ============================================

    function bindEvents() {
        // Pagination - Previous (only on list page)
        if (elements.prevBtn) {
            elements.prevBtn.addEventListener('click', () => {
                if (state.page > FIRST_PAGE) fetchAnimeList(state.page - 1);
            });
        }

        // Pagination - Next (only on list page)
        if (elements.nextBtn) {
            elements.nextBtn.addEventListener('click', () => {
                if (state.page < state.totalPages) fetchAnimeList(state.page + 1);
            });
        }

        // Pagination - Jump (only on list page)
        if (elements.jumpBtn && elements.jumpPage) {
            elements.jumpBtn.addEventListener('click', () => {
                const targetPage = parseInt(elements.jumpPage.value);
                if (targetPage && targetPage >= 1 && targetPage <= state.totalPages) {
                    fetchAnimeList(targetPage);
                    elements.jumpPage.value = '';
                }
            });

            elements.jumpPage.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    elements.jumpBtn.click();
                }
            });
        }

        // Search (only on list page)
        if (elements.searchBtn && elements.searchInput) {
            elements.searchBtn.addEventListener('click', () => {
                const keyword = elements.searchInput.value.trim();
                if (keyword) {
                    searchAnime(keyword);
                }
            });

            elements.searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const keyword = elements.searchInput.value.trim();
                    if (keyword) {
                        searchAnime(keyword);
                    }
                }
            });
        }

        if (elements.clearSearchBtn) {
            elements.clearSearchBtn.addEventListener('click', clearSearch);
        }

        // Preview (only on list page)
        if (elements.previewOverlay) {
            elements.previewOverlay.addEventListener('click', closePreview);
        }
        if (elements.previewImage) {
            elements.previewImage.addEventListener('click', (e) => e.stopPropagation());
        }

        // Update checker - 点击标题检查更新
        if (elements.headerCompact) {
            elements.headerCompact.addEventListener('click', () => {
                checkForUpdate(true);
            });
        }
        if (elements.closeUpdateModal) {
            elements.closeUpdateModal.addEventListener('click', hideUpdateModal);
        }
        if (elements.cancelUpdateBtn) {
            elements.cancelUpdateBtn.addEventListener('click', hideUpdateModal);
        }
        if (elements.downloadUpdateBtn) {
            elements.downloadUpdateBtn.addEventListener('click', downloadUpdate);
        }
        // Close modal when clicking outside
        if (elements.updateModal) {
            elements.updateModal.addEventListener('click', (e) => {
                if (e.target === elements.updateModal) {
                    hideUpdateModal();
                }
            });
        }
    }

    // ============================================
    // Update Checker
    // ============================================

    let updateInfo = null;

    async function checkForUpdate(showModal = true) {
        try {
            const response = await fetch(API_UPDATE_CHECK);
            const data = await response.json();

            if (data.has_update) {
                updateInfo = data;
                // 显示更新提示红点
                if (elements.updateBadge) {
                    elements.updateBadge.classList.add('show');
                }
                // 如果要求显示弹窗，则显示
                if (showModal) {
                    showUpdateModal(data);
                }
                return true;
            } else {
                // 隐藏更新提示红点
                if (elements.updateBadge) {
                    elements.updateBadge.classList.remove('show');
                }
                return false;
            }
        } catch (error) {
            console.error('检查更新失败:', error);
            return false;
        }
    }

    function showUpdateModal(data) {
        if (!elements.updateModal) return;

        // Set version info
        if (elements.currentVersionText) {
            elements.currentVersionText.textContent = data.current_version || '-';
        }
        if (elements.latestVersionText) {
            elements.latestVersionText.textContent = data.latest_version || '-';
        }

        // Show prerelease badge if needed
        if (elements.prereleaseBadge) {
            if (data.is_prerelease) {
                elements.prereleaseBadge.classList.remove(CLS_HIDDEN);
            } else {
                elements.prereleaseBadge.classList.add(CLS_HIDDEN);
            }
        }

        // Set release notes
        if (elements.releaseNotes) {
            const notes = data.release_notes || '暂无更新说明';
            // Convert markdown links to HTML if needed
            const notesHtml = notes
                .replace(/\n/g, '<br>')
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color: #4ecdc4;">$1</a>');
            elements.releaseNotes.innerHTML = notesHtml || '暂无更新说明';
        }

        // Show modal
        elements.updateModal.classList.remove(CLS_HIDDEN);
    }

    function hideUpdateModal() {
        if (elements.updateModal) {
            elements.updateModal.classList.add(CLS_HIDDEN);
        }
    }

    function downloadUpdate() {
        if (!updateInfo || !updateInfo.download_url) {
            alert('下载链接不可用');
            return;
        }

        // Open download URL in new tab/window
        window.open(updateInfo.download_url, '_blank');
        hideUpdateModal();
    }

    // ============================================
    // Favorite Functions
    // ============================================

    async function checkFavoriteUpdates() {
        try {
            const response = await fetch(API_FAVORITE_CHECK);
            const data = await response.json();
            
            if (data.success && data.has_updates) {
                const badge = document.getElementById('favoritesBadge');
                if (badge) {
                    badge.classList.add('show');
                }
            }
        } catch (error) {
            console.error('Error checking favorite updates:', error);
        }
    }

    async function toggleFavorite(animeId, isFavorite) {
        try {
            const endpoint = isFavorite ? API_FAVORITE_REMOVE : API_FAVORITE_ADD;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ anime_id: animeId })
            });
            
            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error toggling favorite:', error);
            return false;
        }
    }

    async function checkIsFavorite(animeId) {
        try {
            const response = await fetch(API_FAVORITE_IS_FAVORITE + '?anime_id=' + animeId);
            const data = await response.json();
            return data.success && data.data && data.data.is_favorite;
        } catch (error) {
            console.error('Error checking favorite status:', error);
            return false;
        }
    }

    async function updateFavoriteButton(animeId, isFavorite) {
        const btn = document.querySelector('.favorite-btn[data-anime-id="' + animeId + '"]');
        if (btn) {
            btn.classList.toggle('active', isFavorite);
            btn.title = isFavorite ? '取消追番' : '追番';
        }
    }

    async function bindFavoriteButtons() {
        const buttons = document.querySelectorAll('.favorite-btn');
        buttons.forEach(btn => {
            const animeId = btn.getAttribute('data-anime-id');
            if (animeId) {
                // Check initial state
                checkIsFavorite(animeId).then(isFav => {
                    updateFavoriteButton(animeId, isFav);
                });
                
                // Bind click event
                btn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const isFav = btn.classList.contains('active');
                    const success = await toggleFavorite(animeId, isFav);
                    if (success) {
                        updateFavoriteButton(animeId, !isFav);
                    }
                });
            }
        });
    }

    // ============================================
    // Theme Functions
    // ============================================

    async function loadTheme() {
        try {
            const response = await fetch(API_SETTINGS_THEME);
            const data = await response.json();
            
            if (data.success && data.data) {
                applyTheme(data.data.theme);
            }
        } catch (error) {
            console.error('Error loading theme:', error);
        }
    }

    function applyTheme(theme) {
        const html = document.documentElement;
        html.classList.remove('theme-dark', 'theme-light');
        
        if (theme === 'system') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            html.classList.add(prefersDark ? 'theme-dark' : 'theme-light');
        } else {
            html.classList.add('theme-' + theme);
        }
    }

    // ============================================
    // Initialization
    // ============================================

    function init() {
        bindEvents();
        fetchAnimeList(INITIAL_PAGE);
        
        // Load theme
        loadTheme();
        
        // Check for favorite updates
        checkFavoriteUpdates();
        
        // Auto check for updates on startup (after a delay, 不显示弹窗)
        setTimeout(() => {
            checkForUpdate(false);
        }, 2000);
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for debugging
    window.Anime1App = {
        state,
        elements,
        fetchAnimeList,
        fetchCoversParallel,
        searchAnime,
        clearSearch,
        openPreview,
        closePreview,
        checkForUpdate,
        toggleFavorite,
        checkIsFavorite
    };
})();
