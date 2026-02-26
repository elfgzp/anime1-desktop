import DOMPurify from 'dompurify'

/**
 * 安全转义文本 - 防止 XSS
 * @param text - 需要转义的文本
 * @returns 转义后的文本
 */
export function escapeText(text: string | null | undefined): string {
  if (text == null) return ''
  return DOMPurify.sanitize(String(text), { ALLOWED_TAGS: [], KEEP_CONTENT: true })
}

/**
 * 安全获取对象属性值
 * @param obj - 目标对象
 * @param attr - 属性名
 * @param defaultValue - 默认值
 * @returns 安全的属性值
 */
export function getSafeAttr(obj: Record<string, any>, attr: string, defaultValue = ''): string {
  const value = obj[attr]
  return escapeText(value || defaultValue)
}

/**
 * 净化番剧列表数据
 * @param list - 番剧列表
 * @returns 净化后的列表
 */
export function sanitizeAnimeList(list: any[]): any[] {
  return list.map(anime => ({
    ...anime,
    title: escapeText(anime.title),
    year: escapeText(anime.year),
    season: escapeText(anime.season),
    subtitleGroup: escapeText(anime.subtitle_group || anime.subtitleGroup)
  }))
}

/**
 * 净化番剧详情数据
 * @param data - 番剧详情数据
 * @returns 净化后的数据
 */
export function sanitizeAnimeData(data: any): any {
  if (!data || !data.anime) return data

  const anime = data.anime
  return {
    ...data,
    anime: {
      ...anime,
      title: escapeText(anime.title),
      year: escapeText(anime.year),
      season: escapeText(anime.season),
      subtitleGroup: escapeText(anime.subtitle_group || anime.subtitleGroup),
      summary: escapeText(anime.summary)
    }
  }
}
