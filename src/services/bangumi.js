/**
 * Bangumi Service for covers with Wikipedia fallback
 */

import axios from 'axios';
import * as cheerio from 'cheerio';
import * as OpenCC from 'opencc-js';
import { getCachedCover, setCachedCover } from './coverCache.js';

const BANGUMI_SEARCH_URL = 'https://bangumi.tv/subject_search/{keyword}?cat=2';
const BANGUMI_BASE_URL = 'https://bangumi.tv';
const WIKIPEDIA_BASE_URL = 'https://zh.wikipedia.org';
const WIKIPEDIA_SEARCH_URL = 'https://zh.wikipedia.org/w/index.php?search={keyword}&title=Special%3ASearch&profile=advanced&fulltext=1&ns0=1';

const http = axios.create({
  timeout: 15000,
  headers: {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
  }
});

const tradToSimpConverter = OpenCC.Converter({ from: 'tw', to: 'cn' });

function extractCoreKeywords(title) {
  if (!title) return '';
  let core = title.replace(/\s*\[\d+\]\s*/g, ' ');
  core = core.replace(/\s*\(\d+\)\s*/g, ' ');
  core = core.replace(/[～~].*$/g, '');
  core = core.replace(/[【】].*$/g, '');
  return core.trim() || title;
}

function calculateSimilarity(title1, title2) {
  if (!title1 || !title2) return 0;
  const clean1 = title1.replace(/[【】\(\)（）\[\]!!！\s～~]/g, '').trim();
  const clean2 = title2.replace(/[【】\(\)（）\[\]!!！\s～~]/g, '').trim();
  if (clean1 === clean2) return 100;
  if (clean1.length >= 3 && clean2.length >= 3) {
    if (clean1.includes(clean2) || clean2.includes(clean1)) return 90;
  }
  const c1 = new Set(clean1.split('').filter(c => c >= '\u4e00' && c <= '\u9fff'));
  const c2 = new Set(clean2.split('').filter(c => c >= '\u4e00' && c <= '\u9fff'));
  if (c1.size >= 2 && c2.size >= 2) {
    const overlap = new Set([...c1].filter(x => c2.has(x)));
    const total = Math.max(c1.size, c2.size);
    const score = Math.round((overlap.size / total) * 100);
    if (score >= 50) return score;
  }
  return 0;
}

async function searchBangumiWeb(keyword) {
  try {
    const cleanKeyword = keyword.replace(/[^\w\u4e00-\u9fa5]/g, ' ').trim();
    const url = BANGUMI_SEARCH_URL.replace('{keyword}', encodeURIComponent(cleanKeyword));
    const response = await http.get(url);
    const $ = cheerio.load(response.data);
    const results = [];
    
    $('li.item').each((_, item) => {
      const $item = $(item);
      const nameElem = $item.find('h3 a');
      const name = nameElem.text().trim();
      const subjectUrl = nameElem.attr('href');
      if (!name) return;
      
      let coverUrl = null;
      const coverLink = $item.find('a.subjectCover');
      if (coverLink.length) {
        const img = coverLink.find('img.cover');
        if (img.length) {
          coverUrl = img.attr('src');
          if (coverUrl && coverUrl.startsWith('//')) coverUrl = 'https:' + coverUrl;
          else if (coverUrl && coverUrl.startsWith('/')) coverUrl = BANGUMI_BASE_URL + coverUrl;
        }
      }
      
      results.push({ 
        name, 
        name_cn: name, 
        cover_url: coverUrl,
        subject_url: subjectUrl ? (subjectUrl.startsWith('http') ? subjectUrl : BANGUMI_BASE_URL + subjectUrl) : null
      });
    });
    
    return results;
  } catch (error) {
    console.error('[Bangumi] Web search error:', keyword, error.message);
    return [];
  }
}

/**
 * Fetch detailed info from Bangumi subject page
 */
async function fetchBangumiDetail(subjectUrl) {
  if (!subjectUrl) return null;
  
  try {
    const url = subjectUrl.startsWith('http') ? subjectUrl : BANGUMI_BASE_URL + subjectUrl;
    const response = await http.get(url);
    const $ = cheerio.load(response.data);
    
    const detail = {
      subject_url: url,
      rating: null,
      rank: null,
      date: null,
      type: null,
      summary: null,
      genres: [],
      staff: [],
      cast: []
    };
    
    // Rating score
    const ratingElem = $('#panelRating .number, .global_score .number, .score_num');
    if (ratingElem.length) {
      const ratingText = ratingElem.text().trim();
      const ratingMatch = ratingText.match(/(\d+\.?\d*)/);
      if (ratingMatch) detail.rating = parseFloat(ratingMatch[1]);
    }
    
    // Rank
    const rankElem = $('.rank .rank_text, .global_rank, .rank_num');
    if (rankElem.length) {
      const rankText = rankElem.text().trim();
      const rankMatch = rankText.match(/(\d+)/);
      if (rankMatch) detail.rank = parseInt(rankMatch[1]);
    }
    
    // Type (TV, Movie, OVA, etc.)
    const typeElem = $('.subject_type, #subject_type');
    if (typeElem.length) {
      detail.type = typeElem.text().trim();
    } else {
      // Try to find in infobox
      const infoboxType = $('#infobox li').filter(function() {
        return $(this).text().includes('类型');
      }).first();
      if (infoboxType.length) {
        detail.type = infoboxType.text().replace(/.*:/, '').trim();
      }
    }
    
    // Air date
    const dateElem = $('#infobox li').filter(function() {
      const text = $(this).text();
      return text.includes('放送开始') || text.includes('上映年度') || text.includes('上映日期');
    }).first();
    if (dateElem.length) {
      detail.date = dateElem.text().replace(/.*:/, '').trim();
    }
    
    // Summary
    const summaryElem = $('#subject_summary, .subject_summary, #columnInSubjectA .text');
    if (summaryElem.length) {
      detail.summary = summaryElem.text().trim();
    }
    
    // Genres
    $('#infobox li').each((_, elem) => {
      const text = $(elem).text();
      if (text.includes('类型') || text.includes('Genre') || text.includes(' genres')) {
        const genres = text.replace(/.*:/, '').split(/[,\/、]/).map(g => g.trim()).filter(g => g);
        detail.genres.push(...genres);
      }
    });
    
    // Staff
    $('.staff, #staffList li, .staff_list li').each((_, elem) => {
      const $elem = $(elem);
      const name = $elem.find('.name, .staff_name').text().trim();
      const role = $elem.find('.role, .staff_role').text().trim();
      if (name && role) {
        detail.staff.push({ name, role });
      }
    });
    
    // Cast (voice actors)
    $('.cast, #castList li, .cast_list li, .actor').each((_, elem) => {
      const $elem = $(elem);
      const name = $elem.find('.name, .actor_name, .voice_actor').text().trim();
      const character = $elem.find('.character, .role_name').text().trim();
      if (name) {
        detail.cast.push({ name, character: character || null });
      }
    });
    
    return detail;
  } catch (error) {
    console.error('[Bangumi] Error fetching detail:', error.message);
    return null;
  }
}

/**
 * Search Wikipedia as fallback
 */
async function searchWikipedia(title) {
  if (!title) return null;
  
  try {
    // Clean title for search
    const cleanTitle = extractCoreKeywords(title);
    const url = WIKIPEDIA_SEARCH_URL.replace('{keyword}', encodeURIComponent(cleanTitle));
    
    const response = await http.get(url);
    const $ = cheerio.load(response.data);
    
    // Try to find the first result link
    const resultLink = $('div.mw-search-result-heading a').first();
    if (!resultLink.length) return null;
    
    const resultTitle = resultLink.text().trim();
    const resultHref = resultLink.attr('href');
    if (!resultHref) return null;
    
    const resultUrl = WIKIPEDIA_BASE_URL + resultHref;
    
    // Fetch the article page to get the cover image
    const articleResponse = await http.get(resultUrl);
    const $article = cheerio.load(articleResponse.data);
    
    let coverUrl = null;
    
    // Try to find image in infobox
    const infobox = $article('table.infobox');
    if (infobox.length) {
      const firstImg = infobox.find('img').first();
      if (firstImg.length) {
        coverUrl = firstImg.attr('src');
      }
    }
    
    // Try to find file link for the main image
    if (!coverUrl) {
      const fileLink = $article('a.image[href*="File:"]').first();
      if (fileLink.length) {
        const fileHref = fileLink.attr('href');
        if (fileHref) {
          const fileUrl = WIKIPEDIA_BASE_URL + fileHref;
          const fileResponse = await http.get(fileUrl);
          const $file = cheerio.load(fileResponse.data);
          const img = $file('img[typeof="mw:File"]').first() || $file('div#file img').first();
          if (img.length) {
            coverUrl = img.attr('src') || img.attr('data-src');
          }
        }
      }
    }
    
    if (!coverUrl) return null;
    
    // Normalize URL
    if (coverUrl.startsWith('//')) coverUrl = 'https:' + coverUrl;
    
    // Try to get larger image
    if (coverUrl.includes('/thumb/')) {
      coverUrl = coverUrl.replace(/\/thumb\//, '/');
      coverUrl = coverUrl.replace(/\/\d+px-[^/]+$/, '');
    }
    
    console.log(`[Wikipedia] Found cover for: ${title} ✓`);
    return { name: resultTitle, cover_url: coverUrl };
    
  } catch (error) {
    console.error('[Wikipedia] Search error:', title, error.message);
    return null;
  }
}

async function searchAnime(title) {
  if (!title) return null;
  
  const cleanTitle = extractCoreKeywords(title);
  
  // Strategy 1: Try Bangumi with original title
  let results = await searchBangumiWeb(cleanTitle);
  if (results.length > 0) {
    const scored = results.map(r => ({
      ...r,
      score: calculateSimilarity(title, r.name_cn || r.name)
    })).sort((a, b) => b.score - a.score);
    // Return best match if score >= 50, otherwise return first result with low confidence
    if (scored[0].score >= 50) return scored[0];
    // Fallback: return first result (like Python version)
    return { ...scored[0], score: 0 };
  }
  
  // Strategy 2: Try Bangumi with Simplified Chinese
  try {
    const simpTitle = tradToSimpConverter(cleanTitle);
    if (simpTitle !== cleanTitle) {
      results = await searchBangumiWeb(simpTitle);
      if (results.length > 0) {
        const scored = results.map(r => ({
          ...r,
          score: calculateSimilarity(title, r.name_cn || r.name)
        })).sort((a, b) => b.score - a.score);
        if (scored[0].score >= 50) return scored[0];
        return { ...scored[0], score: 0 };
      }
    }
  } catch (e) {}
  
  // Strategy 3: Try Bangumi with core keywords
  const coreKeywords = cleanTitle.split(/\s+/)[0];
  if (coreKeywords && coreKeywords !== cleanTitle && coreKeywords.length >= 2) {
    results = await searchBangumiWeb(coreKeywords);
    if (results.length > 0) {
      const scored = results.map(r => ({
        ...r,
        score: calculateSimilarity(coreKeywords, r.name_cn || r.name)
      })).sort((a, b) => b.score - a.score);
      if (scored[0].score >= 30) return scored[0];
      return { ...scored[0], score: 0 };
    }
  }
  
  return null;
}

export async function getCoverUrl(title, animeId = null) {
  if (!title) return null;
  
  // Check persistent cache first
  if (animeId) {
    const cached = getCachedCover(animeId);
    if (cached && cached.cover_url) {
      console.log(`[Cover] Cache hit for: ${title}`);
      return cached.cover_url;
    }
  }
  
  try {
    const result = await searchAnime(title);
    if (!result) {
      console.log('[Cover] No search result for:', title);
      return null;
    }
    
    const coverUrl = result.cover_url;
    
    // Save to persistent cache
    if (animeId && coverUrl) {
      setCachedCover(animeId, title, coverUrl);
    }
    
    return coverUrl;
  } catch (error) {
    console.error('[Cover] Error getting cover for', title, error.message);
    return null;
  }
}

export async function getBatchCovers(animeList) {
  const results = [];
  const batchSize = 3;
  
  for (let i = 0; i < animeList.length; i += batchSize) {
    const batch = animeList.slice(i, i + batchSize);
    const batchPromises = batch.map(async (anime) => {
      const coverUrl = await getCoverUrl(anime.title, anime.id);
      return { id: anime.id, cover_url: coverUrl || '' };
    });
    
    const batchResults = await Promise.all(batchPromises);
    results.push(...batchResults);
    
    if (i + batchSize < animeList.length) {
      await new Promise(r => setTimeout(r, 500));
    }
  }
  
  return results;
}

/**
 * Get full Bangumi info including rating, summary, etc.
 */
export async function getBangumiInfo(title, animeId = null) {
  if (!title) return null;
  
  try {
    // Search for the anime
    const result = await searchAnime(title);
    if (!result || !result.subject_url) {
      console.log('[Bangumi] No subject URL found for:', title);
      return null;
    }
    
    // Fetch detailed info
    const detail = await fetchBangumiDetail(result.subject_url);
    if (!detail) {
      console.log('[Bangumi] Failed to fetch detail for:', title);
      return null;
    }
    
    console.log(`[Bangumi] Got info for: ${title}`, {
      rating: detail.rating,
      rank: detail.rank,
      genres: detail.genres.length
    });
    
    return detail;
  } catch (error) {
    console.error('[Bangumi] Error getting info for', title, error.message);
    return null;
  }
}

export default { getCoverUrl, getBatchCovers, getBangumiInfo };
