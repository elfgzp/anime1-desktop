/* Favorites Page JavaScript */

(function() {
    'use strict';

    const API_FAVORITE_LIST = '/api/favorite/list';
    const CLS_HIDDEN = 'hidden';
    const CLS_SHOW = 'show';

    const elements = {
        grid: document.getElementById('animeGrid'),
        emptyState: document.getElementById('emptyState'),
        loadingOverlay: document.getElementById('loadingOverlay')
    };

    async function loadFavorites() {
        try {
            elements.loadingOverlay.classList.remove(CLS_HIDDEN);
            
            const response = await fetch(API_FAVORITE_LIST);
            const data = await response.json();
            
            if (data.success && data.data) {
                const favorites = data.data;
                
                if (favorites.length === 0) {
                    showEmpty();
                } else {
                    renderFavorites(favorites);
                }
            } else {
                showEmpty();
            }
        } catch (error) {
            console.error('Error loading favorites:', error);
            showEmpty();
        } finally {
            elements.loadingOverlay.classList.add(CLS_HIDDEN);
        }
    }

    function showEmpty() {
        elements.grid.innerHTML = '';
        elements.emptyState.classList.remove(CLS_HIDDEN);
    }

    function renderFavorites(favorites) {
        elements.emptyState.classList.add(CLS_HIDDEN);
        
        elements.grid.innerHTML = favorites.map(fav => {
            const hasUpdate = fav.has_update || (fav.episode > fav.last_episode);
            const updateBadge = hasUpdate ? '<span class="update-badge ' + CLS_SHOW + '" title="有更新"></span>' : '';
            
            return '<a class="anime-card' + (hasUpdate ? ' has-update' : '') + '" href="/anime/' + fav.id + '">' +
                '<div class="card-cover">' +
                (fav.cover_url ? '<img src="' + fav.cover_url + '" alt="' + fav.title + '" onerror="this.style.display=\'none\'">' : '') +
                updateBadge +
                '</div>' +
                '<div class="card-content">' +
                '<div class="card-title">' + fav.title + '</div>' +
                '<div class="card-meta">' +
                '<span class="tag tag-episode">第' + fav.episode + '集</span>' +
                (fav.year ? '<span class="tag tag-year">' + fav.year + '</span>' : '') +
                (fav.season ? '<span class="tag tag-season">' + fav.season + '</span>' : '') +
                (fav.subtitle_group ? '<span class="tag tag-subtitle">' + fav.subtitle_group + '</span>' : '') +
                '</div>' +
                '</div>' +
                '</a>';
        }).join('');
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadFavorites);
    } else {
        loadFavorites();
    }
})();
