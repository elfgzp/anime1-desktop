/**
 * Performance Trace Service for Electron
 * 
 * Features:
 * - Distributed tracing with span tree structure
 * - Performance metrics collection
 * - Trace chain tracking
 * - Performance statistics
 */

import { settingsDB } from './database.js';

// Trace span status
export const SpanStatus = {
  OK: 'ok',
  ERROR: 'error',
  PENDING: 'pending',
};

// Performance rating thresholds (ms)
const RATING_THRESHOLDS = {
  good: 1000,      // < 1s: good
  needsImprovement: 2500,  // < 2.5s: needs improvement
  // >= 2.5s: poor
};

/**
 * Get performance rating based on duration
 */
function getRating(duration) {
  if (duration < RATING_THRESHOLDS.good) return 'good';
  if (duration < RATING_THRESHOLDS.needsImprovement) return 'needs-improvement';
  return 'poor';
}

/**
 * Generate unique ID
 */
function generateId() {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
}

/**
 * Performance Span
 */
export class PerformanceSpan {
  constructor(name, options = {}) {
    this.spanId = generateId();
    this.traceId = options.traceId || generateId();
    this.parentSpanId = options.parentSpanId || null;
    this.name = name;
    this.startTime = Date.now();
    this.endTime = null;
    this.duration = 0;
    this.status = SpanStatus.PENDING;
    this.metadata = options.metadata || {};
    this.children = [];
  }

  finish(status = SpanStatus.OK, metadata = {}) {
    this.endTime = Date.now();
    this.duration = this.endTime - this.startTime;
    this.status = status;
    Object.assign(this.metadata, metadata);
    return this;
  }

  addChild(childSpan) {
    this.children.push(childSpan);
  }

  toJSON() {
    return {
      span_id: this.spanId,
      trace_id: this.traceId,
      parent_span_id: this.parentSpanId,
      name: this.name,
      start_time: this.startTime,
      end_time: this.endTime,
      duration: this.duration,
      status: this.status,
      rating: getRating(this.duration),
      metadata: this.metadata,
      children: this.children.map(c => c.toJSON()),
    };
  }
}

/**
 * Performance Trace
 */
export class PerformanceTrace {
  constructor(rootName, options = {}) {
    this.traceId = generateId();
    this.rootName = rootName;
    this.page = options.page || '';
    this.createdAt = Math.floor(Date.now() / 1000);
    this.spans = new Map();
    this.rootSpan = null;
  }

  startSpan(name, options = {}) {
    const span = new PerformanceSpan(name, {
      traceId: this.traceId,
      parentSpanId: options.parentSpanId,
      metadata: options.metadata,
    });
    
    this.spans.set(span.spanId, span);
    
    if (!this.rootSpan) {
      this.rootSpan = span;
    }
    
    return span;
  }

  finish() {
    if (this.rootSpan) {
      this.rootSpan.finish();
    }
  }

  toJSON() {
    const allSpans = Array.from(this.spans.values());
    const totalDuration = this.rootSpan?.duration || 0;
    
    // Build span tree
    const spanMap = new Map();
    allSpans.forEach(span => {
      spanMap.set(span.spanId, {
        ...span.toJSON(),
        children: [],
      });
    });
    
    // Build tree structure
    const rootSpans = [];
    spanMap.forEach((span, spanId) => {
      if (span.parent_span_id && spanMap.has(span.parent_span_id)) {
        spanMap.get(span.parent_span_id).children.push(span);
      } else {
        rootSpans.push(span);
      }
    });

    // Get all operation names
    const operations = allSpans.map(s => s.name);

    return {
      trace_id: this.traceId,
      root_name: this.rootName,
      page: this.page,
      created_at: this.createdAt,
      total_duration: totalDuration,
      span_count: allSpans.length,
      rating: getRating(totalDuration),
      operations,
      root_spans: rootSpans,
    };
  }
}

/**
 * Performance Service
 */
export class PerformanceService {
  constructor() {
    this._traces = [];
    this._activeTraces = new Map();
    this._maxTraces = 1000; // Keep last 1000 traces
  }

  /**
   * Initialize service
   */
  async init() {
    await this._loadTraces();
  }

  /**
   * Load traces from database
   */
  async _loadTraces() {
    try {
      const saved = await settingsDB.get('performanceTraces');
      if (saved && Array.isArray(saved)) {
        this._traces = saved;
      }
    } catch (error) {
      console.error('[Performance] Error loading traces:', error);
      this._traces = [];
    }
  }

  /**
   * Save traces to database
   */
  async _saveTraces() {
    try {
      // Trim to max traces
      if (this._traces.length > this._maxTraces) {
        this._traces = this._traces.slice(-this._maxTraces);
      }
      await settingsDB.set('performanceTraces', this._traces);
    } catch (error) {
      console.error('[Performance] Error saving traces:', error);
    }
  }

  /**
   * Start a new trace
   */
  startTrace(rootName, options = {}) {
    const trace = new PerformanceTrace(rootName, options);
    this._activeTraces.set(trace.traceId, trace);
    return trace;
  }

  /**
   * Finish and save a trace
   */
  async finishTrace(traceId) {
    const trace = this._activeTraces.get(traceId);
    if (!trace) return null;

    trace.finish();
    const traceData = trace.toJSON();
    
    this._traces.push(traceData);
    this._activeTraces.delete(traceId);
    
    await this._saveTraces();
    return traceData;
  }

  /**
   * Record performance data directly
   */
  async recordPerformance(data) {
    const traceData = {
      trace_id: data.trace_id || generateId(),
      root_name: data.name || 'unknown',
      page: data.page || '',
      created_at: Math.floor(Date.now() / 1000),
      total_duration: data.duration || 0,
      span_count: 1,
      rating: getRating(data.duration || 0),
      operations: [data.name || 'unknown'],
      root_spans: [{
        span_id: generateId(),
        trace_id: data.trace_id || generateId(),
        parent_span_id: null,
        name: data.name || 'unknown',
        start_time: Date.now() - (data.duration || 0),
        end_time: Date.now(),
        duration: data.duration || 0,
        status: data.status || SpanStatus.OK,
        rating: getRating(data.duration || 0),
        metadata: data.metadata || {},
        children: [],
      }],
    };

    this._traces.push(traceData);
    await this._saveTraces();
    return traceData;
  }

  /**
   * Batch record performance data
   */
  async batchRecordPerformance(items) {
    const results = [];
    for (const item of items) {
      const result = await this.recordPerformance(item);
      results.push(result);
    }
    return results;
  }

  /**
   * Get trace by ID
   */
  getTrace(traceId) {
    return this._traces.find(t => t.trace_id === traceId) || null;
  }

  /**
   * Get recent traces with filtering
   */
  getRecentTraces(options = {}) {
    let traces = [...this._traces];

    // Filter by page
    if (options.page) {
      traces = traces.filter(t => t.page === options.page);
    }

    // Filter by operation
    if (options.operation) {
      const op = options.operation.toLowerCase();
      traces = traces.filter(t => 
        t.operations.some(o => o.toLowerCase().includes(op))
      );
    }

    // Filter by trace_id
    if (options.trace_id) {
      traces = traces.filter(t => 
        t.trace_id.toLowerCase().includes(options.trace_id.toLowerCase())
      );
    }

    // Sort
    const sortBy = options.sort_by || 'created_at';
    const sortOrder = options.sort_order || 'desc';
    
    traces.sort((a, b) => {
      let aVal, bVal;
      if (sortBy === 'duration') {
        aVal = a.total_duration;
        bVal = b.total_duration;
      } else {
        aVal = a.created_at;
        bVal = b.created_at;
      }
      return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
    });

    // Pagination
    const limit = options.limit || 50;
    const offset = options.offset || 0;
    const total = traces.length;
    traces = traces.slice(offset, offset + limit);

    return { traces, total };
  }

  /**
   * Get performance statistics
   */
  getStats() {
    const traces = this._traces;
    const count = traces.length;

    if (count === 0) {
      return {
        count: 0,
        avg_duration: 0,
        p50: 0,
        p90: 0,
        p99: 0,
        good_count: 0,
        needs_improvement_count: 0,
        poor_count: 0,
        by_name: {},
      };
    }

    const durations = traces.map(t => t.total_duration).sort((a, b) => a - b);
    
    // Calculate percentiles
    const p50 = this._percentile(durations, 0.5);
    const p90 = this._percentile(durations, 0.9);
    const p99 = this._percentile(durations, 0.99);
    
    // Calculate average
    const avg_duration = durations.reduce((a, b) => a + b, 0) / count;
    
    // Count by rating
    const good_count = traces.filter(t => t.rating === 'good').length;
    const needs_improvement_count = traces.filter(t => t.rating === 'needs-improvement').length;
    const poor_count = traces.filter(t => t.rating === 'poor').length;

    // Stats by operation name
    const byName = {};
    traces.forEach(t => {
      const name = t.root_name;
      if (!byName[name]) {
        byName[name] = { count: 0, total_duration: 0, durations: [] };
      }
      byName[name].count++;
      byName[name].total_duration += t.total_duration;
      byName[name].durations.push(t.total_duration);
    });

    // Calculate stats for each operation
    const by_name = {};
    Object.keys(byName).forEach(name => {
      const data = byName[name];
      const sortedDurations = data.durations.sort((a, b) => a - b);
      by_name[name] = {
        count: data.count,
        avg: data.total_duration / data.count,
        p99: this._percentile(sortedDurations, 0.99),
      };
    });

    return {
      count,
      avg_duration,
      p50,
      p90,
      p99,
      good_count,
      needs_improvement_count,
      poor_count,
      by_name,
    };
  }

  /**
   * Calculate percentile
   */
  _percentile(sortedValues, percentile) {
    if (sortedValues.length === 0) return 0;
    const index = Math.ceil(sortedValues.length * percentile) - 1;
    return sortedValues[Math.max(0, index)];
  }

  /**
   * Clear all performance data
   */
  async clearAllData() {
    this._traces = [];
    this._activeTraces.clear();
    await this._saveTraces();
  }

  /**
   * Get trace chain (for detailed view)
   */
  getTraceChain(traceId) {
    const trace = this.getTrace(traceId);
    if (!trace) return null;

    // Flatten span tree for display
    const spans = [];
    const flatten = (spanList, depth = 0) => {
      for (const span of spanList) {
        spans.push({ ...span, depth });
        if (span.children?.length) {
          flatten(span.children, depth + 1);
        }
      }
    };
    flatten(trace.root_spans);

    return {
      ...trace,
      spans,
    };
  }
}

// Singleton instance
let performanceService = null;

export function getPerformanceService() {
  if (!performanceService) {
    performanceService = new PerformanceService();
  }
  return performanceService;
}

export function resetPerformanceService() {
  if (performanceService) {
    performanceService.clearAllData();
    performanceService = null;
  }
}

export default {
  PerformanceService,
  PerformanceTrace,
  PerformanceSpan,
  SpanStatus,
  getPerformanceService,
  resetPerformanceService,
};
