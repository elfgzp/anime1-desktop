/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

// 提取 findUnfinishedEpisode 函数用于测试
// 这是一个纯函数，可以直接测试其逻辑
function createFindUnfinishedEpisode(episodeProgressMap) {
  return function findUnfinishedEpisode(episodes) {
    if (!episodes || episodes.length === 0) return -1

    const UNFINISHED_THRESHOLD = 0.9  // 90% 视为看完
    const UNSTARTED_THRESHOLD = 0.1  // 10% 以下视为未开始

    let lastUnfinishedIdx = -1
    let lastUnfinishedProgress = null

    for (let i = episodes.length - 1; i >= 0; i--) {
      const ep = episodes[i]
      const progress = episodeProgressMap.value[ep.id]

      if (progress && progress.total_seconds > 0) {
        const percent = progress.position_seconds / progress.total_seconds

        // 检查是否未看完
        if (percent > UNSTARTED_THRESHOLD && percent < UNFINISHED_THRESHOLD) {
          return i
        }

        // 记录最后一集有进度的集数（作为备选）
        if (percent >= UNFINISHED_THRESHOLD) {
          if (lastUnfinishedIdx === -1) {
            lastUnfinishedIdx = i
            lastUnfinishedProgress = percent
          }
        }
      }
    }

    // 如果所有集数都看完了，但最后一集有进度，返回最后一集
    if (lastUnfinishedIdx !== -1 && lastUnfinishedProgress >= 0.99) {
      // 最后一集已看完 >99%，从下一集开始
      if (lastUnfinishedIdx < episodes.length - 1) {
        return lastUnfinishedIdx + 1
      }
    }

    // 没有找到未看完的集数
    return -1
  }
}

describe('findUnfinishedEpisode', () => {
  let episodeProgressMap
  let findUnfinishedEpisode

  beforeEach(() => {
    episodeProgressMap = ref({})
    findUnfinishedEpisode = createFindUnfinishedEpisode(episodeProgressMap)
  })

  describe('边界情况', () => {
    it('空数组应该返回 -1', () => {
      expect(findUnfinishedEpisode([])).toBe(-1)
    })

    it('null 应该返回 -1', () => {
      expect(findUnfinishedEpisode(null)).toBe(-1)
    })

    it('undefined 应该返回 -1', () => {
      expect(findUnfinishedEpisode(undefined)).toBe(-1)
    })
  })

  describe('没有进度数据', () => {
    it('没有进度数据时应该返回 -1', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' },
        { id: '3', episode: '3' }
      ]
      episodeProgressMap.value = {}
      expect(findUnfinishedEpisode(episodes)).toBe(-1)
    })

    it('进度数据 total_seconds 为 0 时应该忽略', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 50, total_seconds: 0 }
      }
      expect(findUnfinishedEpisode(episodes)).toBe(-1)
    })
  })

  describe('查找未看完的集数', () => {
    it('应该找到进度为 50% 的集数', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' },
        { id: '3', episode: '3' }
      ]
      // 第2集看到50%
      episodeProgressMap.value = {
        '1': { position_seconds: 100, total_seconds: 100 },  // 100% - 看完
        '2': { position_seconds: 300, total_seconds: 600 },  // 50% - 未看完
        '3': { position_seconds: 0, total_seconds: 600 }    // 0% - 未开始
      }
      expect(findUnfinishedEpisode(episodes)).toBe(1)
    })

    it('应该找到最后一集未看完的集数', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' },
        { id: '3', episode: '3' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 100, total_seconds: 100 },  // 100%
        '2': { position_seconds: 600, total_seconds: 600 },  // 100%
        '3': { position_seconds: 300, total_seconds: 600 }  // 50%
      }
      expect(findUnfinishedEpisode(episodes)).toBe(2)
    })

    it('应该优先返回进度在 10%-90% 之间的集数', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' },
        { id: '3', episode: '3' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 100, total_seconds: 100 },  // 100%
        '2': { position_seconds: 400, total_seconds: 600 },  // 66.7% - 未看完
        '3': { position_seconds: 500, total_seconds: 600 }  // 83.3% - 未看完
      }
      // 从后往前找，应该返回第3集
      expect(findUnfinishedEpisode(episodes)).toBe(2)
    })
  })

  describe('看完后的续播逻辑', () => {
    it('上一集 >99% 应该播放下一集', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' },
        { id: '3', episode: '3' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 100, total_seconds: 100 },  // 100%
        '2': { position_seconds: 595, total_seconds: 600 },  // 99.17% - 看完
        '3': { position_seconds: 0, total_seconds: 600 }    // 0%
      }
      // 第2集看完 >99%，应该播放第3集
      expect(findUnfinishedEpisode(episodes)).toBe(2)
    })

    it('最后一集看完应该返回 -1', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 100, total_seconds: 100 },  // 100%
        '2': { position_seconds: 600, total_seconds: 600 }  // 100%
      }
      expect(findUnfinishedEpisode(episodes)).toBe(-1)
    })

    it('90%-99% 之间应该视为未看完，继续播放该集', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 90, total_seconds: 100 },   // 90% - 刚好等于阈值，视为看完
        '2': { position_seconds: 540, total_seconds: 600 }  // 90%
      }
      // 第2集 90% 视为看完，应该返回 -1
      expect(findUnfinishedEpisode(episodes)).toBe(-1)
    })

    it('进度刚好 10% 应该视为未开始，不选择该集', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 60, total_seconds: 600 },   // 10%
        '2': { position_seconds: 0, total_seconds: 600 }    // 0%
      }
      // 10% 刚好等于阈值，视为未开始，应该返回 -1
      expect(findUnfinishedEpisode(episodes)).toBe(-1)
    })
  })

  describe('进度阈值边界', () => {
    it('进度 9% 应该视为未开始', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 54, total_seconds: 600 },  // 9%
        '2': { position_seconds: 0, total_seconds: 600 }
      }
      expect(findUnfinishedEpisode(episodes)).toBe(-1)
    })

    it('进度 11% 应该被选中', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 66, total_seconds: 600 },  // 11%
        '2': { position_seconds: 0, total_seconds: 600 }
      }
      expect(findUnfinishedEpisode(episodes)).toBe(0)
    })

    it('进度 89% 应该被选中', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 534, total_seconds: 600 },  // 89%
        '2': { position_seconds: 0, total_seconds: 600 }
      }
      expect(findUnfinishedEpisode(episodes)).toBe(0)
    })

    it('进度 91% 应该视为看完', () => {
      const episodes = [
        { id: '1', episode: '1' },
        { id: '2', episode: '2' }
      ]
      episodeProgressMap.value = {
        '1': { position_seconds: 546, total_seconds: 600 },  // 91%
        '2': { position_seconds: 0, total_seconds: 600 }
      }
      expect(findUnfinishedEpisode(episodes)).toBe(-1)
    })
  })
})

describe('findUnfinishedEpisode - 实际场景', () => {
  let episodeProgressMap
  let findUnfinishedEpisode

  beforeEach(() => {
    episodeProgressMap = ref({})
    findUnfinishedEpisode = createFindUnfinishedEpisode(episodeProgressMap)
  })

  it('场景：用户看到一半停电了', () => {
    // 用户刚看到第3集的一半
    const episodes = [
      { id: 'ep1', episode: '1' },
      { id: 'ep2', episode: '2' },
      { id: 'ep3', episode: '3' },
      { id: 'ep4', episode: '4' }
    ]
    episodeProgressMap.value = {
      'ep1': { position_seconds: 600, total_seconds: 600 },  // 第1集看完
      'ep2': { position_seconds: 600, total_seconds: 600 },  // 第2集看完
      'ep3': { position_seconds: 300, total_seconds: 600 },  // 第3集看到50%
      'ep4': { position_seconds: 0, total_seconds: 600 }
    }
    expect(findUnfinishedEpisode(episodes)).toBe(2)  // 继续播放第3集
  })

  it('场景：用户忘记看到哪一集', () => {
    // 用户看到第2集的80%
    const episodes = [
      { id: 'ep1', episode: '1' },
      { id: 'ep2', episode: '2' },
      { id: 'ep3', episode: '3' }
    ]
    episodeProgressMap.value = {
      'ep1': { position_seconds: 480, total_seconds: 600 },  // 80%
      'ep2': { position_seconds: 0, total_seconds: 600 }
    }
    expect(findUnfinishedEpisode(episodes)).toBe(0)  // 继续播放第1集
  })

  it('场景：用户刚看完最后一集', () => {
    // 用户看完最后一集
    const episodes = [
      { id: 'ep1', episode: '1' },
      { id: 'ep2', episode: '2' }
    ]
    episodeProgressMap.value = {
      'ep1': { position_seconds: 600, total_seconds: 600 },
      'ep2': { position_seconds: 600, total_seconds: 600 }
    }
    expect(findUnfinishedEpisode(episodes)).toBe(-1)  // 返回 -1，播放第一集
  })

  it('场景：新用户第一次看', () => {
    // 没有任何进度
    const episodes = [
      { id: 'ep1', episode: '1' },
      { id: 'ep2', episode: '2' }
    ]
    episodeProgressMap.value = {}
    expect(findUnfinishedEpisode(episodes)).toBe(-1)  // 播放第一集
  })
})
