"""后端链路追踪工具 - 类似 OpenTelemetry 规范"""
import json
import logging
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

# Context variables for trace propagation
_current_trace_id = ContextVar('trace_id', default=None)
_current_span_id = ContextVar('span_id', default=None)

# 是否启用追踪 (开发模式)
_tracing_enabled = True

# 递归深度保护
_recursion_depth = 0
_max_recursion_depth = 50


def is_tracing_enabled():
    """检查是否启用追踪"""
    return _tracing_enabled


def set_tracing_enabled(enabled):
    """设置是否启用追踪"""
    global _tracing_enabled
    _tracing_enabled = enabled


def generate_span_id():
    """生成 span ID"""
    return uuid.uuid4().hex[:16]


def get_trace_id():
    """获取当前 trace_id"""
    return _current_trace_id.get()


def get_span_id():
    """获取当前 span_id"""
    return _current_span_id.get()


def start_trace(trace_id=None):
    """开始一个追踪"""
    if not _tracing_enabled:
        return None

    trace_id = trace_id or f"trace_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    _current_trace_id.set(trace_id)
    _current_span_id.set(None)
    return trace_id


def end_trace():
    """结束当前追踪"""
    _current_trace_id.set(None)
    _current_span_id.set(None)


def trace_operation(name, trace_type='operation'):
    """装饰器：追踪函数执行"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _tracing_enabled:
                return func(*args, **kwargs)

            start = time.time()
            parent_span_id = _current_span_id.get()
            span_id = generate_span_id()
            _current_span_id.set(span_id)

            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000

                # 记录到数据库
                _record_span(
                    trace_id=_current_trace_id.get(),
                    parent_span_id=parent_span_id,
                    span_id=span_id,
                    name=name,
                    trace_type=trace_type,
                    duration=duration,
                    start_time=start,
                    success=True
                )

                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                _record_span(
                    trace_id=_current_trace_id.get(),
                    parent_span_id=parent_span_id,
                    span_id=span_id,
                    name=name,
                    trace_type=trace_type,
                    duration=duration,
                    start_time=start,
                    success=False,
                    error=str(e)
                )
                raise
            finally:
                _current_span_id.set(parent_span_id)

        return wrapper
    return decorator


class TraceSpan:
    """追踪 span 记录器"""
    def __init__(self, name, trace_type='operation', metadata=None):
        if not _tracing_enabled:
            self._active = False
            return

        self.name = name
        self.trace_type = trace_type
        self.metadata = metadata or {}
        self._active = True
        self._start_time = time.time()
        self._parent_span_id = _current_span_id.get()
        self._span_id = generate_span_id()
        _current_span_id.set(self._span_id)

    def end(self, success=True, error=None):
        """结束 span"""
        if not _tracing_enabled or not self._active:
            return

        duration = (time.time() - self._start_time) * 1000
        _record_span(
            trace_id=_current_trace_id.get(),
            parent_span_id=self._parent_span_id,
            span_id=self._span_id,
            name=self.name,
            trace_type=self.trace_type,
            duration=duration,
            start_time=self._start_time,
            success=success,
            error=error,
            metadata=self.metadata
        )

        _current_span_id.set(self._parent_span_id)
        self._active = False

    def __enter__(self):
        """支持 with 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.end(success=False, error=str(exc_val))
        else:
            self.end(success=True)
        return False


def _record_span(trace_id, parent_span_id, span_id, name, trace_type,
                 duration, start_time, success, error=None, metadata=None):
    """记录 span 到数据库"""
    global _recursion_depth, _tracing_enabled

    if not trace_id:
        return

    # 防止递归过深
    if _recursion_depth > _max_recursion_depth:
        logger.warning('[Trace] Skipping span record due to max recursion depth')
        return

    _recursion_depth += 1
    # 在 try 块之外获取值，确保 finally 中一定能访问
    original_enabled = _tracing_enabled
    try:
        # 禁用追踪后保存到数据库，避免递归
        _tracing_enabled = False

        try:
            from src.models.performance_trace import PerformanceTrace

            end_time = start_time + (duration / 1000)

            try:
                PerformanceTrace.create(
                    trace_id=trace_id,
                    parent_span_id=parent_span_id,
                    span_id=span_id,
                    trace_type=trace_type,
                    name=name,
                    page=None,
                    duration=duration,
                    start_time=start_time,
                    end_time=end_time,
                    rating='good' if (success and duration < 1000) else ('needs-improvement' if (success and duration < 2500) else 'poor'),
                    metadata=json.dumps({
                        'success': success,
                        'error': error,
                        **(metadata or {})
                    }, ensure_ascii=False)
                )
            except Exception as db_error:
                # 数据库锁定或其他错误，静默忽略避免级联失败
                logger.debug(f'[Trace] Failed to save span: {db_error}')
        finally:
            _tracing_enabled = original_enabled

    except Exception as e:
        logger.warning(f'[Trace] Error in _record_span: {e}')
    finally:
        _recursion_depth -= 1


# 便捷函数
def trace_api(name):
    """追踪 API 调用"""
    return trace_operation(name, 'api_call')


def trace_db(name):
    """追踪数据库操作"""
    return trace_operation(name, 'db_query')


def trace_external(name):
    """追踪外部 API 调用"""
    return trace_operation(name, 'external_api')


def get_current_trace_context():
    """获取当前追踪上下文"""
    return {
        'trace_id': _current_trace_id.get(),
        'span_id': _current_span_id.get()
    }
