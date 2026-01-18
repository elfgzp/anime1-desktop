"""性能追踪数据模型 - 支持链路追踪"""
import json
from datetime import datetime
from peewee import (
    TextField,
    FloatField,
    TimestampField,
    IntegerField,
)

from src.models.database import BaseModel


class PerformanceTrace(BaseModel):
    """性能追踪记录表"""

    # 链路追踪ID - 关联同一请求的所有操作
    trace_id = TextField(index=True)

    # 父span ID - 用于构建调用链
    parent_span_id = TextField(null=True, index=True)

    # 当前span ID
    span_id = TextField(unique=True)

    # 追踪类型: page_load, api_call, function, component
    trace_type = TextField()

    # 操作名称
    name = TextField()

    # 页面路径
    page = TextField(null=True)

    # 耗时 (毫秒)
    duration = FloatField()

    # 开始时间戳 (毫秒)
    start_time = FloatField()

    # 结束时间戳 (毫秒)
    end_time = FloatField()

    # 评分: good, needs-improvement, poor
    rating = TextField(null=True)

    # 元数据 (JSON格式)
    metadata = TextField(null=True)

    # 创建时间
    created_at = TimestampField(default=datetime.now)

    class Meta:
        table_name = 'performance_traces'
        indexes = [
            # 按 trace_id 查询完整链路
            (('trace_id',), False),
            # 按创建时间查询最近记录
            (('created_at',), False),
            # 按页面和类型查询
            (('page', 'trace_type'), False),
        ]


class PerformanceStat(BaseModel):
    """性能统计表 - 存储聚合数据"""

    # 统计维度
    name = TextField(index=True)
    trace_type = TextField(index=True)
    page = TextField(null=True)

    # 统计周期 (小时)
    hour_bucket = TimestampField(index=True)

    # 统计数据
    count = IntegerField(default=0)
    avg_duration = FloatField()
    min_duration = FloatField()
    max_duration = FloatField()

    # P50, P90, P99
    p50 = FloatField()
    p90 = FloatField()
    p99 = FloatField()

    # 评分分布
    good_count = IntegerField(default=0)
    needs_improvement_count = IntegerField(default=0)
    poor_count = IntegerField(default=0)

    # 创建/更新时间
    updated_at = TimestampField(default=datetime.now)

    class Meta:
        table_name = 'performance_stats'
        indexes = [
            (('name', 'hour_bucket'), False),
        ]


def init_performance_tables():
    """初始化性能追踪表"""
    db = __import__('src.models.database', fromlist=['get_database']).get_database()
    db.create_tables([PerformanceTrace, PerformanceStat])
    return True


def clear_performance_traces() -> int:
    """清空 performance_traces 表的所有记录

    Returns:
        删除的记录数量
    """
    db = __import__('src.models.database', fromlist=['get_database']).get_database()
    count = PerformanceTrace.delete().execute()
    return count


def clear_performance_stats() -> int:
    """清空 performance_stats 表的所有记录

    Returns:
        删除的记录数量
    """
    db = __import__('src.models.database', fromlist=['get_database']).get_database()
    count = PerformanceStat.delete().execute()
    return count
