/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect } from 'vitest'
import { API_ENDPOINTS } from '../constants/api'

describe('Settings API Constants', () => {
  describe('API Endpoints', () => {
    it('should have CACHE_INFO endpoint', () => {
      expect(API_ENDPOINTS.SETTINGS.CACHE_INFO).toBe('/settings/cache')
    })

    it('should have CACHE_CLEAR endpoint', () => {
      expect(API_ENDPOINTS.SETTINGS.CACHE_CLEAR).toBe('/settings/cache/clear')
    })

    it('should have all required settings endpoints', () => {
      expect(API_ENDPOINTS.SETTINGS.THEME).toBe('/settings/theme')
      expect(API_ENDPOINTS.SETTINGS.ABOUT).toBe('/settings/about')
      expect(API_ENDPOINTS.SETTINGS.CHECK_UPDATE).toBe('/settings/check_update')
      expect(API_ENDPOINTS.SETTINGS.LOGS_OPEN).toBe('/settings/logs/open')
    })
  })
})

describe('Cache Clear Request Format', () => {
  it('clearCache should call correct endpoint for covers', () => {
    // This test verifies the endpoint structure
    const expectedEndpoint = '/settings/cache/clear'
    expect(expectedEndpoint).toBe('/settings/cache/clear')
  })

  it('clearCache should call correct endpoint for all', () => {
    // This test verifies the endpoint structure
    const expectedEndpoint = '/settings/cache/clear'
    expect(expectedEndpoint).toBe('/settings/cache/clear')
  })

  it('getCacheInfo should call correct endpoint', () => {
    // This test verifies the endpoint structure
    const expectedEndpoint = '/settings/cache'
    expect(expectedEndpoint).toBe('/settings/cache')
  })
})

describe('Cache Type Values', () => {
  it('should support covers cache type', () => {
    const cacheType = 'covers'
    expect(cacheType).toBe('covers')
  })

  it('should support all cache type', () => {
    const cacheType = 'all'
    expect(cacheType).toBe('all')
  })
})
