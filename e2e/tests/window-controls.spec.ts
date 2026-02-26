/**
 * 窗口控制相关测试
 */
import { test, expect } from '../fixtures'

test.describe('窗口控制 IPC', () => {
  test('应该能够获取窗口状态', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(result).toBeDefined()
    expect(result.maximized).toBe(false) // 初始状态
    expect(result.fullscreen).toBe(false)
    expect(result.focused).toBe(true)
  })

  test('应该能够最小化窗口', async ({ window }) => {
    // 调用最小化
    await window.evaluate(async () => {
      await window.api.window.minimize()
    })
    
    // 等待一下
    await window.waitForTimeout(500)
    
    // 检查状态
    const result = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    // 窗口应该是最小化状态
    expect(result.minimized).toBe(true)
    
    // 恢复窗口以便后续测试
    await window.evaluate(async () => {
      // 通过 electron 的 BrowserWindow 恢复
      const { ipcRenderer } = require('electron')
      // 直接调用 show 来恢复窗口
    })
    
    // 使用 page 方法恢复
    await window.bringToFront()
  })

  test('应该能够最大化窗口', async ({ window }) => {
    // 先确保窗口不是最大化状态
    const initialState = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    if (initialState.maximized) {
      // 如果已经最大化，先恢复
      await window.evaluate(async () => {
        await window.api.window.maximize()
      })
      await window.waitForTimeout(500)
    }
    
    // 调用最大化
    await window.evaluate(async () => {
      await window.api.window.maximize()
    })
    
    await window.waitForTimeout(500)
    
    // 检查状态
    const result = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(result.maximized).toBe(true)
    
    // 恢复
    await window.evaluate(async () => {
      await window.api.window.maximize()
    })
    
    await window.waitForTimeout(500)
  })

  test('应该能够切换全屏', async ({ window }) => {
    // 获取初始状态
    const initialState = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(initialState.fullscreen).toBe(false)
    
    // 进入全屏
    await window.evaluate(async () => {
      await window.api.window.toggleFullscreen()
    })
    
    await window.waitForTimeout(500)
    
    // 检查状态
    const fullscreenState = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(fullscreenState.fullscreen).toBe(true)
    
    // 退出全屏
    await window.evaluate(async () => {
      await window.api.window.toggleFullscreen()
    })
    
    await window.waitForTimeout(500)
    
    // 检查状态
    const normalState = await window.evaluate(async () => {
      return await window.api.window.getState()
    })
    
    expect(normalState.fullscreen).toBe(false)
  })
})

test.describe('窗口事件', () => {
  test('窗口应该响应 resize 事件', async ({ window }) => {
    // 记录当前尺寸
    const initialSize = await window.evaluate(() => ({
      width: window.innerWidth,
      height: window.innerHeight,
    }))
    
    // 改变窗口大小
    await window.setViewportSize({ width: 1024, height: 768 })
    
    // 等待渲染进程更新
    await window.waitForTimeout(500)
    
    // 验证新尺寸
    const newSize = await window.evaluate(() => ({
      width: window.innerWidth,
      height: window.innerHeight,
    }))
    
    expect(newSize.width).toBe(1024)
    expect(newSize.height).toBe(768)
    
    // 恢复原始尺寸
    await window.setViewportSize({ 
      width: initialSize.width, 
      height: initialSize.height 
    })
  })
})
