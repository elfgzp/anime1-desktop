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
        searchOverlay: document.getElementById(ID_SEARCH_OVERLAY)
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

            // Parallel fetch covers (过滤掉18x番剧)
            if (data.anime_list.length > 0) {
                await fetchCoversParallel(data.anime_list);
            }
        } catch (error) {
            console.error(TEXT_LOADING_FAILED, error);
            showEmpty();
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

    async function fetchCoversParallel(animeList) {
        // 过滤掉18x番剧（标题包含🔞或链接到 anime1.pw）
        const normalAnime = animeList.filter(anime =>
            !anime.title.includes(ADULT_MARKER) && !anime.detail_url.includes(ADULT_SITE_DOMAIN)
        );

        const promises = normalAnime.map(anime =>
            fetch(API_COVERS + '?ids=' + anime.id)
                .then(res => res.json())
                .then(data => ({ animeId: anime.id, data: data[0] || null }))
                .catch(() => ({ animeId: anime.id, data: null }))
        );

        for (const promise of promises) {
            try {
                const result = await promise;
                if (result.data && result.data.cover_url) {
                    updateAnimeRow(result.animeId, result.data);
                }
            } catch (e) {
                console.error(TEXT_IMAGE_FAILED, e);
            }
        }
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
            return;
        }

        elements.content.classList.remove(CLS_HIDDEN);
        elements.emptyState.classList.add(CLS_HIDDEN);

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
                coverHtml = '<span class="loading-placeholder">⏳</span>';
            }

            return '<a id="anime-card-' + animeId + '" class="anime-card' + (isAdult ? '' : ' card-loading') + '" href="/anime/' + animeId + '">' +
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
                '</a>';
        }).join('');
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
    }

    // ============================================
    // Initialization
    // ============================================

    function init() {
        bindEvents();
        fetchAnimeList(INITIAL_PAGE);
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
        closePreview
    };
})();
