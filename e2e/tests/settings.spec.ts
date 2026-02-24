/**
 * 设置页相关测试
 */
import { test, expect } from '../fixtures'
import { SettingsPage } from '../pages'

test.describe('设置页', () => {
  test('设置页应该正确加载', async ({ window }) => {
    const settingsPage = new SettingsPage(window)
    
    await settingsPage.goto()
    
    // 验证 URL
    expect(window.url()).toContain('/settings')
    
    // 验证页面内容加载
    const hasContent = await settingsPage.hasText('设置') || 
                      await settingsPage.hasText('Settings')
    expect(hasContent).toBe(true)
  })

  test('应该显示版本信息', async ({ window }) => {
    const settingsPage = new SettingsPage(window)
    
    await settingsPage.goto()
    await window.waitForTimeout(1000)
    
    // 通过 IPC 获取版本
    const result = await window.evaluate(async () => {
      const settings = await window.api.settings.getAll()
      return settings
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
  })
})

test.describe('设置修改', () => {
  test('应该能够修改设置值', async ({ window }) => {
    const settingsPage = new SettingsPage(window)
    
    await settingsPage.goto()
    
    // 测试设置一个值
    const testKey = 'test_setting'
    const testValue = 'test_value_' + Date.now()
    
    const result = await window.evaluate(async ({ key, value }) => {
      return await window.api.settings.set({ key, value })
    }, { key: testKey, value: testValue })
    
    expect(result.success).toBe(true)
    
    // 验证设置已保存
    const getResult = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    
    expect(getResult.success).toBe(true)
    expect(getResult.data).toBe(testValue)
  })

  test('设置应该持久化', async ({ window }) => {
    const settingsPage = new SettingsPage(window)
    
    await settingsPage.goto()
    
    // 设置一个测试值
    const testKey = 'persist_test'
    const testValue = 'persist_value_' + Date.now()
    
    await window.evaluate(async ({ key, value }) => {
      await window.api.settings.set({ key, value })
    }, { key: testKey, value: testValue })
    
    // 刷新页面
    await window.reload()
    await window.waitForTimeout(2000)
    
    // 验证设置还在
    const result = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    
    expect(result.success).toBe(true)
    expect(result.data).toBe(testValue)
  })
})

test.describe('IPC 设置接口', () => {
  test('应该能够获取所有设置', async ({ window }) => {
    const result = await window.evaluate(async () => {
      return await window.api.settings.getAll()
    })
    
    expect(result).toBeDefined()
    expect(result.success).toBe(true)
    expect(typeof result.data).toBe('object')
  })

  test('应该能够设置和获取单个设置', async ({ window }) => {
    const testKey = 'single_test'
    const testValue = 'single_value'
    
    // 设置
    const setResult = await window.evaluate(async ({ key, value }) => {
      return await window.api.settings.set({ key, value })
    }, { key: testKey, value: testValue })
    
    expect(setResult.success).toBe(true)
    
    // 获取
    const getResult = await window.evaluate(async (key) => {
      return await window.api.settings.get({ key })
    }, testKey)
    
    expect(getResult.success).toBe(true)
    expect(getResult.data).toBe(testValue)
  })
})
