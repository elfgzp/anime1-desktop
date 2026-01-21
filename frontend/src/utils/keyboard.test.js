/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { KEYBOARD_KEYS } from '@/constants/keyboard'

// 提取键盘快捷键处理函数用于测试
function createHandleKeydown(getPlayer) {
  return function handleKeydown(event) {
    const player = getPlayer()
    if (!player) return

    // 如果焦点在输入框等元素上，不处理
    const tagName = event.target.tagName.toLowerCase()
    if (tagName === 'input' || tagName === 'textarea' || event.target.isContentEditable) {
      return
    }

    const jumpTime = 10  // 跳10秒

    switch (event.key) {
      case KEYBOARD_KEYS.ARROW_LEFT:
        event.preventDefault()
        const leftTime = Math.max(0, player.currentTime() - jumpTime)
        player.currentTime(leftTime)
        break
      case KEYBOARD_KEYS.ARROW_RIGHT:
        event.preventDefault()
        const rightTime = Math.min(player.duration(), player.currentTime() + jumpTime)
        player.currentTime(rightTime)
        break
      case KEYBOARD_KEYS.SPACE:
      case KEYBOARD_KEYS.K:
        event.preventDefault()
        if (player.paused()) {
          player.play()
        } else {
          player.pause()
        }
        break
    }
  }
}

// 创建 mock player
function createMockPlayer(options = {}) {
  const {
    currentTime = 0,
    duration = 600,
    paused = true
  } = options

  // 使用对象来存储状态
  const state = {
    time: currentTime,
    isPaused: paused
  }

  return {
    currentTime: vi.fn(function(value) {
      if (value !== undefined) {
        state.time = value
      }
      return state.time
    }),
    duration: vi.fn(() => duration),
    paused: vi.fn(() => state.isPaused),
    play: vi.fn(() => {
      state.isPaused = false
    }),
    pause: vi.fn(() => {
      state.isPaused = true
    }),
    // 辅助方法
    getTime: () => state.time,
    getPaused: () => state.isPaused,
    resetTime: () => { state.time = 0 },
    setPaused: (p) => { state.isPaused = p },
    setTime: (t) => { state.time = t }
  }
}

// 创建 mock 事件对象
function createMockKeyboardEvent(options = {}) {
  const { key = '', target = null } = options
  const mockTarget = target || { tagName: 'DIV', isContentEditable: false }

  return {
    key,
    target: mockTarget,
    preventDefault: vi.fn()
  }
}

describe('键盘快捷键处理', () => {
  let player
  let getPlayer

  beforeEach(() => {
    vi.clearAllMocks()
    player = createMockPlayer({ currentTime: 100, duration: 600, paused: true })
    getPlayer = () => player
  })

  describe('player 为 null', () => {
    it('player 为 null 时不应该报错', () => {
      const handleKeydown = createHandleKeydown(() => null)
      const event = createMockKeyboardEvent({ key: 'ArrowLeft' })
      expect(() => handleKeydown(event)).not.toThrow()
    })
  })

  describe('输入框忽略', () => {
    it('焦点在 input 上应该忽略', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.ARROW_LEFT,
        target: { tagName: 'INPUT', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).not.toHaveBeenCalled()
      expect(player.play).not.toHaveBeenCalled()
      expect(player.pause).not.toHaveBeenCalled()
    })

    it('焦点在 textarea 上应该忽略', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.SPACE,
        target: { tagName: 'TEXTAREA', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).not.toHaveBeenCalled()
      expect(player.play).not.toHaveBeenCalled()
      expect(player.pause).not.toHaveBeenCalled()
    })

    it('焦点在 contentEditable 元素上应该忽略', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.K,
        target: { tagName: 'DIV', isContentEditable: true }
      })

      handleKeydown(event)

      expect(player.currentTime).not.toHaveBeenCalled()
      expect(player.play).not.toHaveBeenCalled()
      expect(player.pause).not.toHaveBeenCalled()
    })
  })

  describe('快退快捷键', () => {
    it('左箭头应该快退 10 秒', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      player.setTime(100)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.ARROW_LEFT,
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).toHaveBeenCalledWith(90)
      expect(event.preventDefault).toHaveBeenCalled()
    })

    it('快退时不应该低于 0', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      player.setTime(5)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.ARROW_LEFT,
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).toHaveBeenCalledWith(0)
    })

    it('从 0 继续快退应该保持在 0', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      player.setTime(0)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.ARROW_LEFT,
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).toHaveBeenCalledWith(0)
    })
  })

  describe('快进快捷键', () => {
    it('右箭头应该快进 10 秒', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      player.setTime(100)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.ARROW_RIGHT,
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).toHaveBeenCalledWith(110)
    })

    it('快进时不应该超过视频总时长', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      player.setTime(595)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.ARROW_RIGHT,
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).toHaveBeenCalledWith(600)
    })

    it('刚好在结尾时快进应该保持在结尾', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      player.setTime(600)
      const event = createMockKeyboardEvent({
        key: KEYBOARD_KEYS.ARROW_RIGHT,
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).toHaveBeenCalledWith(600)
    })
  })

  describe('播放/暂停快捷键', () => {
    describe('空格键', () => {
      it('暂停时按空格应该播放', () => {
        const handleKeydown = createHandleKeydown(getPlayer)
        // beforeEach 设置 paused: true，不需要额外操作
        const event = createMockKeyboardEvent({
          key: KEYBOARD_KEYS.SPACE,
          target: { tagName: 'DIV', isContentEditable: false }
        })

        handleKeydown(event)

        expect(player.play).toHaveBeenCalled()
        expect(player.pause).not.toHaveBeenCalled()
        expect(event.preventDefault).toHaveBeenCalled()
      })

      it('播放时按空格应该暂停', () => {
        const handleKeydown = createHandleKeydown(getPlayer)
        player.setPaused(false)
        const event = createMockKeyboardEvent({
          key: KEYBOARD_KEYS.SPACE,
          target: { tagName: 'DIV', isContentEditable: false }
        })

        handleKeydown(event)

        expect(player.pause).toHaveBeenCalled()
        expect(player.play).not.toHaveBeenCalled()
      })
    })

    describe('K 键', () => {
      it('暂停时按 K 应该播放', () => {
        const handleKeydown = createHandleKeydown(getPlayer)
        // beforeEach 设置 paused: true，不需要额外操作
        const event = createMockKeyboardEvent({
          key: KEYBOARD_KEYS.K,
          target: { tagName: 'DIV', isContentEditable: false }
        })

        handleKeydown(event)

        expect(player.play).toHaveBeenCalled()
        expect(player.pause).not.toHaveBeenCalled()
      })

      it('播放时按 K 应该暂停', () => {
        const handleKeydown = createHandleKeydown(getPlayer)
        player.setPaused(false)
        const event = createMockKeyboardEvent({
          key: KEYBOARD_KEYS.K,
          target: { tagName: 'DIV', isContentEditable: false }
        })

        handleKeydown(event)

        expect(player.pause).toHaveBeenCalled()
        expect(player.play).not.toHaveBeenCalled()
      })
    })
  })

  describe('其他按键', () => {
    it('其他按键不应该触发任何操作', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      player.setTime(100)
      const event = createMockKeyboardEvent({
        key: 'a',
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).not.toHaveBeenCalled()
      expect(player.play).not.toHaveBeenCalled()
      expect(player.pause).not.toHaveBeenCalled()
    })

    it('Escape 键不应该触发任何操作', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      const event = createMockKeyboardEvent({
        key: 'Escape',
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).not.toHaveBeenCalled()
      expect(player.play).not.toHaveBeenCalled()
      expect(player.pause).not.toHaveBeenCalled()
    })

    it('Enter 键不应该触发任何操作', () => {
      const handleKeydown = createHandleKeydown(getPlayer)
      const event = createMockKeyboardEvent({
        key: 'Enter',
        target: { tagName: 'DIV', isContentEditable: false }
      })

      handleKeydown(event)

      expect(player.currentTime).not.toHaveBeenCalled()
      expect(player.play).not.toHaveBeenCalled()
      expect(player.pause).not.toHaveBeenCalled()
    })
  })
})

describe('键盘快捷键 - 实际场景', () => {
  let player
  let getPlayer

  beforeEach(() => {
    vi.clearAllMocks()
    player = createMockPlayer({ currentTime: 300, duration: 600, paused: false })
    getPlayer = () => player
  })

  it('场景：用户想快退 10 秒回顾', () => {
    const handleKeydown = createHandleKeydown(getPlayer)
    // 用户在 300 秒处，想往回看一点
    player.setTime(300)
    const event = createMockKeyboardEvent({
      key: 'ArrowLeft',
      target: { tagName: 'DIV', isContentEditable: false }
    })

    handleKeydown(event)

    expect(player.currentTime).toHaveBeenCalledWith(290)
  })

  it('场景：用户跳过片头', () => {
    const handleKeydown = createHandleKeydown(getPlayer)
    // 用户在 600 秒视频的第 50 秒，想跳过前 10 秒
    player.setTime(50)
    const event = createMockKeyboardEvent({
      key: 'ArrowRight',
      target: { tagName: 'DIV', isContentEditable: false }
    })

    handleKeydown(event)

    expect(player.currentTime).toHaveBeenCalledWith(60)
  })

  it('场景：接电话时暂停视频', () => {
    const handleKeydown = createHandleKeydown(getPlayer)
    // 视频正在播放，来电话了
    // beforeEach 已经设置 paused: false，不需要额外操作
    const event = createMockKeyboardEvent({
      key: ' ',
      target: { tagName: 'DIV', isContentEditable: false }
    })

    handleKeydown(event)

    expect(player.pause).toHaveBeenCalled()
  })

  it('场景：想继续观看时按 K 键', () => {
    const handleKeydown = createHandleKeydown(getPlayer)
    // 视频暂停了
    player.setPaused(true)
    const event = createMockKeyboardEvent({
      key: 'k',
      target: { tagName: 'DIV', isContentEditable: false }
    })

    handleKeydown(event)

    expect(player.play).toHaveBeenCalled()
  })

  it('场景：在搜索框输入时不应该触发快捷键', () => {
    const handleKeydown = createHandleKeydown(getPlayer)
    // 用户在输入框搜索
    const event = createMockKeyboardEvent({
      key: 'ArrowLeft',
      target: { tagName: 'INPUT', isContentEditable: false }
    })

    handleKeydown(event)

    expect(player.currentTime).not.toHaveBeenCalled()
  })
})
