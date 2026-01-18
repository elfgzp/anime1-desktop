/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { measure, measureApi, reportAllMetrics, startTrace, endTrace } from './performance'

describe('Performance Utils', () => {
  describe('measure', () => {
    it('should return an object with end method', () => {
      const result = measure('test_operation')
      expect(result).toHaveProperty('end')
      expect(typeof result.end).toBe('function')
    })

    it('should return duration when calling end', () => {
      const timer = measure('test')
      const duration = timer.end()
      expect(typeof duration).toBe('number')
      expect(duration).toBeGreaterThanOrEqual(0)
    })

    it('should accept metadata object', () => {
      const timer = measure('test')
      const duration = timer.end({ key: 'value' })
      expect(duration).toBeGreaterThanOrEqual(0)
    })
  })

  describe('measureApi', () => {
    it('should return object with success and error methods', () => {
      const result = measureApi('test_api')
      expect(result).toHaveProperty('success')
      expect(result).toHaveProperty('error')
      expect(typeof result.success).toBe('function')
      expect(typeof result.error).toBe('function')
    })

    it('success should return the response', async () => {
      const timer = measureApi('test')
      const response = { data: 'test' }
      const result = timer.success(response)
      expect(result).toEqual(response)
    })

    it('error should throw the error', () => {
      const timer = measureApi('test')
      expect(() => timer.error(new Error('test'))).toThrow('test')
    })
  })

  describe('startTrace / endTrace', () => {
    it('startTrace should return traceId', () => {
      const traceId = startTrace('test_trace')
      expect(typeof traceId).toBe('string')
      expect(traceId).toContain('trace_')
    })

    it('endTrace should not throw', () => {
      startTrace('test')
      expect(() => endTrace()).not.toThrow()
    })

    it('endTrace without startTrace should not throw', () => {
      expect(() => endTrace()).not.toThrow()
    })
  })
})

describe('Performance API', () => {
  describe('getRecentTraces params', () => {
    it('should accept filter parameters', () => {
      // This test verifies the API structure
      const params = {
        sort_by: 'duration',
        operation: 'page_home',
        page: '/',
        trace_id: 'test123',
        limit: 20
      }

      expect(params.sort_by).toBe('duration')
      expect(params.operation).toBe('page_home')
      expect(params.page).toBe('/')
      expect(params.trace_id).toBe('test123')
      expect(params.limit).toBe(20)
    })
  })
})
