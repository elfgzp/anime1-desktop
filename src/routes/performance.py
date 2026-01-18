"""性能追踪路由 - 接收前端性能数据上报并支持链路追踪"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from src.models.performance_trace import PerformanceTrace, PerformanceStat

logger = logging.getLogger(__name__)

# 创建蓝图
performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')


def generate_span_id():
    """生成span ID"""
    return uuid.uuid4().hex[:16]


def get_trace_type(name):
    """根据名称判断trace类型"""
    if name.startswith('web-vital_'):
        return 'web_vital'
    elif name.startswith('api_'):
        return 'api_call'
    elif name.startswith('custom_'):
        return 'function'
    elif name.startswith('component_'):
        return 'component'
    elif name.startswith('page_'):
        return 'page_load'
    else:
        return 'operation'


@performance_bp.route('', methods=['POST'])
def record_performance():
    """接收前端性能数据 - 支持链路追踪"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # 提取数据
        name = data.get('name', 'unknown')
        value = data.get('value', 0)
        rating = data.get('rating', 'unknown')
        page = data.get('page', 'unknown')
        timestamp = data.get('timestamp', 0)
        trace_id = data.get('trace_id')
        parent_span_id = data.get('parent_span_id')

        # 生成 span_id
        span_id = generate_span_id()

        # 确定 trace_type
        trace_type = get_trace_type(name)

        # 计算时间戳
        start_time = timestamp / 1000  # 转换为秒
        end_time = start_time + (value / 1000)

        # 保存到数据库
        trace = PerformanceTrace.create(
            trace_id=trace_id or span_id,
            parent_span_id=parent_span_id,
            span_id=span_id,
            trace_type=trace_type,
            name=name,
            page=page,
            duration=float(value),
            start_time=start_time,
            end_time=end_time,
            rating=rating,
            metadata=json.dumps(data.get('metadata', {}))
        )

        logger.info(f"[PERF] {name}={value}ms rating={rating} page={page} span_id={span_id[:8]}")

        return jsonify({
            'success': True,
            'span_id': span_id,
            'trace_id': trace.trace_id
        }), 200

    except Exception as e:
        logger.error(f"[PERF] Error recording performance: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/batch', methods=['POST'])
def batch_record_performance():
    """批量接收性能数据 - 用于一次上报多个span"""
    try:
        data = request.get_json()
        if not data or 'spans' not in data:
            return jsonify({'success': False, 'error': 'No spans provided'}), 400

        spans = data['spans']
        trace_id = data.get('trace_id', generate_span_id())
        results = []

        for span in spans:
            name = span.get('name', 'unknown')
            value = span.get('value', 0)
            rating = span.get('rating', 'unknown')
            page = span.get('page', 'unknown')
            timestamp = span.get('timestamp', 0)
            parent_span_id = span.get('parent_span_id')

            span_id = generate_span_id()
            trace_type = get_trace_type(name)
            start_time = timestamp / 1000
            end_time = start_time + (value / 1000)

            trace = PerformanceTrace.create(
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                span_id=span_id,
                trace_type=trace_type,
                name=name,
                page=page,
                duration=float(value),
                start_time=start_time,
                end_time=end_time,
                rating=rating,
                metadata=json.dumps(span.get('metadata', {}))
            )

            results.append({
                'name': name,
                'span_id': span_id,
                'duration': value
            })

        logger.info(f"[PERF] Batch recorded {len(results)} spans for trace {trace_id[:8]}")

        return jsonify({
            'success': True,
            'trace_id': trace_id,
            'results': results
        }), 200

    except Exception as e:
        logger.error(f"[PERF] Error batch recording: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/trace/<trace_id>', methods=['GET'])
def get_trace_chain(trace_id):
    """获取完整的链路追踪"""
    try:
        # 获取该trace_id的所有span
        traces = PerformanceTrace.select().where(
            PerformanceTrace.trace_id == trace_id
        ).order_by(PerformanceTrace.start_time)

        if not traces:
            return jsonify({'success': False, 'error': 'Trace not found'}), 404

        # 构建树形结构
        span_map = {}
        root_spans = []

        for trace in traces:
            span = {
                'span_id': trace.span_id,
                'parent_span_id': trace.parent_span_id,
                'name': trace.name,
                'trace_type': trace.trace_type,
                'duration': trace.duration,
                'start_time': trace.start_time,
                'end_time': trace.end_time,
                'rating': trace.rating,
                'metadata': json.loads(trace.metadata or '{}'),
                'children': []
            }
            span_map[trace.span_id] = span

        # 构建父子关系
        for span in span_map.values():
            parent_id = span['parent_span_id']
            if parent_id and parent_id in span_map:
                span_map[parent_id]['children'].append(span)
            else:
                root_spans.append(span)

        # 计算总耗时
        total_duration = max(s['end_time'] for s in span_map.values()) - min(s['start_time'] for s in span_map.values())

        return jsonify({
            'success': True,
            'trace_id': trace_id,
            'total_duration': total_duration * 1000,
            'span_count': len(span_map),
            'root_spans': root_spans,
            'created_at': min(t.created_at.timestamp() for t in traces) if traces else None
        })

    except Exception as e:
        logger.error(f"[PERF] Error getting trace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/recent', methods=['GET'])
def get_recent_traces():
    """获取最近的链路追踪列表"""
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))  # 翻页偏移量
        sort_by = request.args.get('sort_by', 'created_at')  # 支持: created_at, duration
        sort_order = request.args.get('sort_order', 'desc')  # 支持: asc, desc
        operation = request.args.get('operation')  # 操作名称过滤（模糊匹配链路中任意span）
        page = request.args.get('page')  # 页面过滤
        trace_id = request.args.get('trace_id')  # 按 trace_id 搜索（支持完整ID或前缀匹配）

        # 获取所有记录用于分组
        query = PerformanceTrace.select().order_by(PerformanceTrace.created_at.desc()).limit(limit * 20)

        # 按 trace_id 分组，构建链路信息
        trace_groups = {}
        for trace in query:
            tid = trace.trace_id
            if tid not in trace_groups:
                trace_groups[tid] = {
                    'trace_id': tid,
                    'page': trace.page,
                    'start_time': trace.start_time,
                    'created_at': trace.created_at.timestamp() if trace.created_at else None,
                    'duration': trace.duration,
                    'rating': trace.rating,
                    'span_count': 0,
                    'root_name': trace.name,
                    'operations': set(),  # 收集链路中所有操作名
                    'total_duration': 0,  # 链路总耗时
                    'max_duration': 0  # 单个span最大耗时
                }
            group = trace_groups[tid]
            group['span_count'] += 1
            group['operations'].add(trace.name)
            group['total_duration'] += trace.duration
            if trace.duration > group['max_duration']:
                group['max_duration'] = trace.duration
                group['duration'] = trace.duration
                group['rating'] = trace.rating

        # 转换为列表并应用过滤
        result = []
        for group in trace_groups.values():
            group['operations'] = list(group['operations'])  # 转换为列表

            # 按 trace_id 搜索（支持完整ID或前缀匹配）
            if trace_id:
                group_tid = group['trace_id']
                # 支持精确匹配或前缀匹配（如用户输入前8位也能搜索到）
                if trace_id != group_tid and not group_tid.startswith(trace_id):
                    continue

            # 按页面过滤（链路的任一页面匹配即可）
            if page and page not in group.get('page', ''):
                continue

            # 按操作名称模糊过滤（链路的任一操作匹配即可）
            if operation:
                matched = any(operation.lower() in op.lower() for op in group['operations'])
                if not matched:
                    continue

            result.append(group)

        # 按指定字段排序
        reverse = sort_order == 'desc'
        if sort_by == 'duration':
            result.sort(key=lambda x: x['duration'], reverse=reverse)
        else:
            result.sort(key=lambda x: x['start_time'], reverse=reverse)

        # 应用分页
        total = len(result)
        paginated_result = result[offset:offset + limit]

        return jsonify({
            'success': True,
            'traces': paginated_result,
            'total': total,
            'offset': offset,
            'limit': limit,
            'filters': {
                'operation': operation,
                'page': page,
                'trace_id': trace_id,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        })

    except Exception as e:
        logger.error(f"[PERF] Error getting recent traces: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/stats', methods=['GET'])
def get_performance_stats():
    """获取性能统计"""
    try:
        hours = int(request.args.get('hours', 24))
        name = request.args.get('name')

        # 计算时间范围
        since = datetime.now() - timedelta(hours=hours)

        query = PerformanceTrace.select().where(
            PerformanceTrace.created_at >= since
        )

        if name:
            query = query.where(PerformanceTrace.name == name)

        traces = list(query)

        if not traces:
            return jsonify({
                'success': True,
                'stats': {
                    'count': 0,
                    'avg_duration': 0,
                    'p50': 0,
                    'p90': 0,
                    'p99': 0
                }
            })

        # 计算统计
        durations = sorted([t.duration for t in traces])
        count = len(durations)

        def percentile(data, q):
            idx = int(len(data) * q / 100)
            return data[idx] if idx < len(data) else data[-1]

        stats = {
            'count': count,
            'avg_duration': sum(durations) / count,
            'min_duration': min(durations),
            'max_duration': max(durations),
            'p50': percentile(durations, 50),
            'p90': percentile(durations, 90),
            'p99': percentile(durations, 99),
            'good_count': sum(1 for t in traces if t.rating == 'good'),
            'needs_improvement_count': sum(1 for t in traces if t.rating == 'needs-improvement'),
            'poor_count': sum(1 for t in traces if t.rating == 'poor'),
            'by_name': {}
        }

        # 按名称分组统计
        name_groups = {}
        for trace in traces:
            if trace.name not in name_groups:
                name_groups[trace.name] = []
            name_groups[trace.name].append(trace.duration)

        for name, durs in name_groups.items():
            durs = sorted(durs)
            stats['by_name'][name] = {
                'count': len(durs),
                'avg': sum(durs) / len(durs),
                'p50': percentile(durs, 50),
                'p90': percentile(durs, 90),
                'p99': percentile(durs, 99)
            }

        return jsonify({
            'success': True,
            'stats': stats,
            'time_range': f'{hours} hours'
        })

    except Exception as e:
        logger.error(f"[PERF] Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@performance_bp.route('/clear', methods=['POST'])
def clear_performance_data():
    """清理性能数据"""
    try:
        clear_all = request.args.get('clear_all', 'false').lower() == 'true'
        days = int(request.args.get('days', 7))

        if clear_all:
            # 清空所有链路追踪数据
            deleted = PerformanceTrace.delete().execute()
            logger.info(f"[PERF] Cleared all {deleted} performance records")
        else:
            # 只删除指定天数前的数据
            cutoff = datetime.now() - timedelta(days=days)
            deleted = PerformanceTrace.delete().where(
                PerformanceTrace.created_at < cutoff
            ).execute()
            logger.info(f"[PERF] Cleared {deleted} performance records older than {days} days")

        return jsonify({
            'success': True,
            'deleted': deleted,
            'clear_all': clear_all
        })

    except Exception as e:
        logger.error(f"[PERF] Error clearing data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
