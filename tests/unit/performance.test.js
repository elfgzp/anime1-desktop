import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  PerformanceService,
  PerformanceTrace,
  PerformanceSpan,
  SpanStatus,
  getPerformanceService,
  resetPerformanceService,
} from '../../src/services/performance.js'

describe('Performance Service', () => {
  let service

  beforeEach(() => {
    service = new PerformanceService()
  })

  afterEach(() => {
    resetPerformanceService()
  })

  describe('PerformanceSpan', () => {
    it('should create a span with correct properties', () => {
      const span = new PerformanceSpan('test-operation', {
        metadata: { key: 'value' },
      })

      expect(span.name).toBe('test-operation')
      expect(span.metadata).toEqual({ key: 'value' })
      expect(span.status).toBe(SpanStatus.PENDING)
      expect(span.spanId).toBeDefined()
      expect(span.traceId).toBeDefined()
    })

    it('should finish span and calculate duration', async () => {
      const span = new PerformanceSpan('test')
      
      await new Promise(resolve => setTimeout(resolve, 10))
      span.finish(SpanStatus.OK, { result: 'success' })

      expect(span.status).toBe(SpanStatus.OK)
      expect(span.duration).toBeGreaterThanOrEqual(10)
      expect(span.metadata.result).toBe('success')
    })

    it('should convert to JSON correctly', () => {
      const span = new PerformanceSpan('test')
      span.finish(SpanStatus.OK)

      const json = span.toJSON()
      expect(json.name).toBe('test')
      expect(json.status).toBe(SpanStatus.OK)
      expect(json.rating).toBeDefined()
      expect(json.children).toEqual([])
    })
  })

  describe('PerformanceTrace', () => {
    it('should create a trace with root span', () => {
      const trace = new PerformanceTrace('test-trace', { page: '/test' })
      const span = trace.startSpan('root-operation')

      expect(trace.traceId).toBeDefined()
      expect(trace.rootName).toBe('test-trace')
      expect(trace.page).toBe('/test')
      expect(span.traceId).toBe(trace.traceId)
    })

    it('should build span tree correctly', () => {
      const trace = new PerformanceTrace('test')
      const root = trace.startSpan('root')
      const child = trace.startSpan('child', { parentSpanId: root.spanId })
      const grandchild = trace.startSpan('grandchild', { parentSpanId: child.spanId })

      trace.finish()

      const json = trace.toJSON()
      expect(json.span_count).toBe(3)
      expect(json.operations).toContain('root')
      expect(json.operations).toContain('child')
      expect(json.operations).toContain('grandchild')
    })
  })

  describe('PerformanceService - Stats', () => {
    it('should return empty stats when no traces', () => {
      const stats = service.getStats()
      
      expect(stats.count).toBe(0)
      expect(stats.avg_duration).toBe(0)
      expect(stats.p50).toBe(0)
      expect(stats.p90).toBe(0)
      expect(stats.p99).toBe(0)
    })

    it('should calculate percentiles correctly', async () => {
      // Add traces with known durations
      for (let i = 1; i <= 10; i++) {
        await service.recordPerformance({
          name: `test-${i}`,
          duration: i * 100,
        })
      }

      const stats = service.getStats()
      
      expect(stats.count).toBe(10)
      expect(stats.p50).toBeGreaterThan(0)
      expect(stats.p90).toBeGreaterThan(0)
      expect(stats.avg_duration).toBeGreaterThan(0)
    })

    it('should categorize ratings correctly', async () => {
      // Good: < 1000ms
      await service.recordPerformance({ name: 'good', duration: 500 })
      
      // Needs improvement: < 2500ms
      await service.recordPerformance({ name: 'ok', duration: 1500 })
      
      // Poor: >= 2500ms
      await service.recordPerformance({ name: 'poor', duration: 3000 })

      const stats = service.getStats()
      
      expect(stats.good_count).toBe(1)
      expect(stats.needs_improvement_count).toBe(1)
      expect(stats.poor_count).toBe(1)
    })
  })

  describe('PerformanceService - Traces', () => {
    it('should record performance data', async () => {
      const result = await service.recordPerformance({
        name: 'api-call',
        duration: 100,
        metadata: { endpoint: '/api/test' },
      })

      expect(result).toBeDefined()
      expect(result.root_name).toBe('api-call')
      expect(result.total_duration).toBe(100)
      expect(result.trace_id).toBeDefined()
    })

    it('should batch record performance data', async () => {
      const items = [
        { name: 'call-1', duration: 100 },
        { name: 'call-2', duration: 200 },
        { name: 'call-3', duration: 300 },
      ]

      const results = await service.batchRecordPerformance(items)
      
      expect(results).toHaveLength(3)
      expect(service.getStats().count).toBe(3)
    })

    it('should get trace by ID', async () => {
      const recorded = await service.recordPerformance({
        name: 'test',
        duration: 100,
      })

      const trace = service.getTrace(recorded.trace_id)
      
      expect(trace).toBeDefined()
      expect(trace.trace_id).toBe(recorded.trace_id)
    })

    it('should filter traces by page', async () => {
      await service.recordPerformance({ name: 'test-1', page: '/home' })
      await service.recordPerformance({ name: 'test-2', page: '/detail' })
      await service.recordPerformance({ name: 'test-3', page: '/home' })

      const { traces, total } = service.getRecentTraces({ page: '/home' })
      
      expect(total).toBe(2)
      expect(traces.every(t => t.page === '/home')).toBe(true)
    })

    it('should sort traces by duration', async () => {
      await service.recordPerformance({ name: 'slow', duration: 300 })
      await service.recordPerformance({ name: 'fast', duration: 100 })
      await service.recordPerformance({ name: 'medium', duration: 200 })

      const { traces } = service.getRecentTraces({ 
        sort_by: 'duration', 
        sort_order: 'desc' 
      })
      
      expect(traces[0].root_name).toBe('slow')
      expect(traces[2].root_name).toBe('fast')
    })
  })

  describe('PerformanceService - Pagination', () => {
    it('should paginate traces correctly', async () => {
      // Add 10 traces
      for (let i = 0; i < 10; i++) {
        await service.recordPerformance({ name: `test-${i}`, duration: 100 })
      }

      const { traces, total } = service.getRecentTraces({ 
        limit: 5, 
        offset: 0 
      })
      
      expect(traces).toHaveLength(5)
      expect(total).toBe(10)
    })
  })

  describe('PerformanceService - Clear Data', () => {
    it('should clear all data', async () => {
      await service.recordPerformance({ name: 'test', duration: 100 })
      expect(service.getStats().count).toBe(1)

      await service.clearAllData()
      
      expect(service.getStats().count).toBe(0)
      expect(service.getRecentTraces().traces).toHaveLength(0)
    })
  })
})
