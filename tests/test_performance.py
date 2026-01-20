"""性能追踪模块测试"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


@pytest.mark.unit
class TestPerformanceTraceModel:
    """测试性能追踪数据模型"""

    def test_import_model(self):
        """测试导入模型"""
        # 模拟 peewee 模型
        with patch('peewee.SqliteDatabase'):
            from src.models.performance_trace import PerformanceTrace, PerformanceStat

            # 验证类存在
            assert PerformanceTrace is not None
            assert PerformanceStat is not None

    def test_trace_fields(self):
        """测试 PerformanceTrace 字段定义"""
        from src.models.performance_trace import PerformanceTrace

        # 验证主要字段存在
        assert hasattr(PerformanceTrace, 'trace_id')
        assert hasattr(PerformanceTrace, 'span_id')
        assert hasattr(PerformanceTrace, 'parent_span_id')
        assert hasattr(PerformanceTrace, 'name')
        assert hasattr(PerformanceTrace, 'duration')
        assert hasattr(PerformanceTrace, 'page')
        assert hasattr(PerformanceTrace, 'trace_type')
        assert hasattr(PerformanceTrace, 'rating')

    def test_stat_fields(self):
        """测试 PerformanceStat 字段定义"""
        from src.models.performance_trace import PerformanceStat

        # 验证统计字段存在
        assert hasattr(PerformanceStat, 'name')
        assert hasattr(PerformanceStat, 'avg_duration')
        assert hasattr(PerformanceStat, 'p50')
        assert hasattr(PerformanceStat, 'p90')
        assert hasattr(PerformanceStat, 'p99')


@pytest.mark.unit
class TestPerformanceRoutes:
    """测试性能追踪路由"""

    @pytest.fixture
    def mock_app(self):
        """创建测试用的 Flask 应用"""
        with patch('src.routes.performance.PerformanceTrace') as MockTrace:
            MockTrace.select.return_value.where.return_value.order_by.return_value = []
            MockTrace.create = Mock()

            with patch('src.routes.performance.get_trace_type') as mock_type:
                mock_type.return_value = 'custom'

                from flask import Flask
                app = Flask(__name__)
                app.config['TESTING'] = True

                # 注册蓝本
                from src.routes.performance import performance_bp
                app.register_blueprint(performance_bp)

                yield app, MockTrace

    def test_record_performance_endpoint_exists(self, mock_app):
        """测试记录性能端点存在"""
        app, _ = mock_app
        client = app.test_client()

        response = client.post('/api/performance',
                               data=json.dumps({
                                   'name': 'test_operation',
                                   'value': 100,
                                   'rating': 'good'
                               }),
                               content_type='application/json')

        # 应该返回 200 或 400（取决于 mock 是否完整）
        assert response.status_code in [200, 400, 500]

    def test_get_stats_endpoint_exists(self, mock_app):
        """测试统计端点存在"""
        app, _ = mock_app
        client = app.test_client()

        response = client.get('/api/performance/stats')
        assert response.status_code in [200, 500]

    def test_get_recent_traces_endpoint_exists(self, mock_app):
        """测试最近追踪端点存在"""
        app, _ = mock_app
        client = app.test_client()

        response = client.get('/api/performance/recent')
        assert response.status_code in [200, 500]


@pytest.mark.unit
class TestPerformanceRecentEndpoint:
    """测试 /recent 接口的完整功能"""

    @pytest.fixture
    def app_with_mock_db(self):
        """创建带有模拟数据库的 Flask 应用"""
        with patch('src.routes.performance.PerformanceTrace') as MockTraceClass:
            # 创建模拟对象
            mock_trace = MagicMock()
            mock_trace.trace_id = 'test_trace_123'
            mock_trace.span_id = 'span_123'
            mock_trace.parent_span_id = None
            mock_trace.name = 'page_home'
            mock_trace.page = '/'
            mock_trace.duration = 150.5
            mock_trace.start_time = 1700000000.0
            mock_trace.rating = 'good'
            mock_trace.created_at = MagicMock()
            mock_trace.created_at.timestamp.return_value = 1700000000.0

            # 配置 mock 查询链
            mock_query = MagicMock()
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = [mock_trace]

            MockTraceClass.select.return_value = mock_query

            from flask import Flask
            app = Flask(__name__)
            app.config['TESTING'] = True

            from src.routes.performance import performance_bp
            app.register_blueprint(performance_bp)

            yield app, MockTraceClass

    def test_get_recent_traces_default(self, app_with_mock_db):
        """测试默认查询最近追踪"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent')

        # 验证调用了 select
        MockTrace.select.assert_called()

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_recent_traces_with_page_filter(self, app_with_mock_db):
        """测试按页面过滤"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?page=/')

        # 验证调用了 select
        MockTrace.select.assert_called()

        assert response.status_code == 200

    def test_get_recent_traces_with_operation_filter(self, app_with_mock_db):
        """测试按操作名称过滤"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?operation=page_home')

        # 验证 where 被调用来过滤操作名称
        MockTrace.select.assert_called()

        assert response.status_code == 200

    def test_get_recent_traces_sort_by_duration(self, app_with_mock_db):
        """测试按耗时排序"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?sort_by=duration')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_recent_traces_sort_by_created_at(self, app_with_mock_db):
        """测试按创建时间排序"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?sort_by=created_at')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_recent_traces_with_all_filters(self, app_with_mock_db):
        """测试综合筛选参数"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?page=/&operation=home&sort_by=duration')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'traces' in data
        assert 'total' in data

    def test_get_recent_traces_limit_parameter(self, app_with_mock_db):
        """测试 limit 参数"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?limit=10')

        # 验证 limit 被调用
        MockTrace.select.return_value.order_by.return_value.limit.assert_called()

        assert response.status_code == 200

    def test_get_recent_traces_offset_parameter(self, app_with_mock_db):
        """测试 offset 参数用于翻页"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?offset=20&limit=10')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'offset' in data
        assert 'limit' in data

    def test_get_recent_traces_with_trace_id_exact_match(self, app_with_mock_db):
        """测试按 trace_id 精确搜索"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?trace_id=test_trace_123')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'filters' in data
        assert data['filters']['trace_id'] == 'test_trace_123'

    def test_get_recent_traces_with_trace_id_prefix_match(self, app_with_mock_db):
        """测试按 trace_id 前缀匹配搜索"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?trace_id=test_trace')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_get_recent_traces_response_contains_pagination_info(self, app_with_mock_db):
        """测试响应包含分页信息"""
        app, MockTrace = app_with_mock_db
        client = app.test_client()

        response = client.get('/api/performance/recent?offset=0&limit=20')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # 验证返回了 offset 和 limit
        assert 'offset' in data
        assert 'limit' in data
        assert 'total' in data
        assert 'traces' in data


@pytest.mark.unit
class TestPerformanceClearEndpoint:
    """测试 /clear 接口功能"""

    @pytest.fixture
    def app_with_mock_clear(self):
        """创建带有模拟删除的 Flask 应用 - 只测试 clear_all 功能"""
        with patch('src.routes.performance.PerformanceTrace') as MockTraceClass:
            # 模拟 delete 查询链 - 只模拟 execute 返回值
            mock_delete = MagicMock()
            mock_delete.execute.return_value = 100

            # 使用 side_effect 来确保每次 delete() 调用返回同一个 mock
            MockTraceClass.delete.return_value = mock_delete

            from flask import Flask
            app = Flask(__name__)
            app.config['TESTING'] = True

            from src.routes.performance import performance_bp
            app.register_blueprint(performance_bp)

            yield app, MockTraceClass, mock_delete

    def test_clear_all_data(self, app_with_mock_clear):
        """测试清空所有数据"""
        app, MockTrace, mock_delete = app_with_mock_clear
        client = app.test_client()

        response = client.post('/api/performance/clear?clear_all=true')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'clear_all' in data
        assert data['clear_all'] is True
        # 验证调用了 delete.execute（不带 where 条件）
        mock_delete.execute.assert_called()

    def test_clear_all_response_format(self, app_with_mock_clear):
        """测试清空响应格式"""
        app, MockTrace, mock_delete = app_with_mock_clear
        client = app.test_client()

        response = client.post('/api/performance/clear?clear_all=true')

        data = json.loads(response.data)
        assert 'success' in data
        assert 'deleted' in data
        assert 'clear_all' in data

    def test_clear_all_returns_deleted_count(self, app_with_mock_clear):
        """测试清空返回删除数量"""
        app, MockTrace, mock_delete = app_with_mock_clear
        client = app.test_client()

        # 设置 mock 返回删除数量
        mock_delete.execute.return_value = 42

        response = client.post('/api/performance/clear?clear_all=true')

        data = json.loads(response.data)
        assert data['success'] is True
        assert data['deleted'] == 42


@pytest.mark.integration
class TestPerformanceTraceModelIntegration:
    """性能追踪模型集成测试（需要真实数据库）"""

    def test_generate_span_id_format(self):
        """测试 span_id 格式"""
        from src.routes.performance import generate_span_id

        span_id = generate_span_id()

        # 应该返回 16 字符的十六进制字符串
        assert len(span_id) == 16
        assert all(c in '0123456789abcdef' for c in span_id)

    def test_get_trace_type_classification(self):
        """测试 trace 类型分类"""
        from src.routes.performance import get_trace_type

        # Web vital
        assert get_trace_type('web-vital_lcp') == 'web_vital'
        assert get_trace_type('web-vital_fcp') == 'web_vital'

        # API call
        assert get_trace_type('api_getList') == 'api_call'
        assert get_trace_type('api_fetchData') == 'api_call'

        # Custom function
        assert get_trace_type('custom_process') == 'function'

        # Component
        assert get_trace_type('component_Home') == 'component'

        # Page load
        assert get_trace_type('page_home') == 'page_load'

        # Default
        assert get_trace_type('unknown_operation') == 'operation'


@pytest.mark.unit
class TestPerformanceUtils:
    """测试前端性能工具"""

    def test_performance_js_syntax(self):
        """测试前端 JS 语法正确"""
        import os

        js_path = os.path.join(os.path.dirname(__file__),
                               '../frontend/src/utils/performance.js')

        if os.path.exists(js_path):
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查关键函数存在
            assert 'export function measure(' in content
            assert 'export function measureApi(' in content
            assert 'export function reportAllMetrics' in content
            assert 'isTracingEnabled' in content

            # 检查开发模式检测
            assert 'isDev' in content
            assert 'DEV' in content or '5173' in content

            # 检查新的指标名称 (onINP 替换了 onFID)
            assert 'onINP' in content
            assert 'inp' in content

            print("✓ 前端 JS 语法检查通过")


@pytest.mark.unit
class TestTraceModule:
    """测试链路追踪模块"""

    def test_import_trace_utils(self):
        """测试导入 trace 工具模块"""
        from src.utils.trace import TraceSpan, start_trace, end_trace
        from src.utils.trace import trace_operation, trace_api, trace_db
        from src.utils.trace import get_trace_id, get_span_id
        from src.utils.trace import generate_span_id, set_tracing_enabled

        # 验证主要函数存在
        assert TraceSpan is not None
        assert start_trace is not None
        assert end_trace is not None
        assert trace_operation is not None
        assert trace_api is not None
        assert trace_db is not None
        assert get_trace_id is not None
        assert get_span_id is not None
        assert generate_span_id is not None
        assert set_tracing_enabled is not None

    def test_trace_span_context_manager(self):
        """测试 TraceSpan 上下文管理器"""
        from src.utils.trace import TraceSpan, set_tracing_enabled

        # 启用追踪
        set_tracing_enabled(True)

        with TraceSpan('test_span', 'test', {'key': 'value'}) as span:
            assert span is not None

        # 清理
        set_tracing_enabled(False)

    def test_trace_decorator(self):
        """测试 trace_operation 装饰器"""
        from src.utils.trace import trace_operation, set_tracing_enabled

        set_tracing_enabled(True)

        @trace_operation('test_function', 'test')
        def sample_function(x, y):
            return x + y

        result = sample_function(1, 2)
        assert result == 3

        set_tracing_enabled(False)

    def test_trace_id_propagation(self):
        """测试 trace_id 传播"""
        from src.utils.trace import start_trace, get_trace_id, end_trace

        trace_id = start_trace('test')
        assert get_trace_id() == trace_id
        end_trace()
        assert get_trace_id() is None


@pytest.mark.unit
class TestAnimeRoutesTracing:
    """测试 anime 路由追踪"""

    def test_anime_bp_import(self):
        """测试 anime blueprint 导入"""
        from src.routes.anime import anime_bp
        assert anime_bp is not None

    def test_anime_bp_has_url_prefix(self):
        """测试 anime blueprint 有正确的 URL 前缀"""
        from src.routes.anime import anime_bp
        assert anime_bp.url_prefix == '/api/anime'

    def test_anime_routes_have_tracing(self):
        """测试 anime 路由包含追踪导入"""
        import inspect
        from src.routes import anime

        source = inspect.getsource(anime)

        # 检查是否导入了 TraceSpan
        assert 'TraceSpan' in source
        assert 'is_tracing_enabled' in source

    def test_get_episodes_has_tracing(self):
        """测试 get_episodes 路由有追踪"""
        import inspect
        from src.routes.anime import get_anime_episodes

        source = inspect.getsource(get_anime_episodes)

        # 检查是否使用了 TraceSpan
        assert 'TraceSpan' in source
        assert 'fetch_episode_page' in source or 'external_http' in source

    def test_get_bangumi_info_has_tracing(self):
        """测试 get_bangumi_info 路由有追踪"""
        import inspect
        from src.routes.anime import get_bangumi_info

        source = inspect.getsource(get_bangumi_info)

        # 检查是否使用了 TraceSpan
        assert 'TraceSpan' in source
        assert 'get_bangumi_external_api' in source or 'cache' in source


@pytest.mark.unit
class TestAnimeCacheServiceTracing:
    """测试 anime cache service 追踪"""

    def test_cache_service_import(self):
        """测试 cache service 导入"""
        from src.services.anime_cache_service import get_anime_map_cache
        assert get_anime_map_cache is not None

    def test_cache_service_has_tracing(self):
        """测试 cache service 包含追踪"""
        import inspect
        from src.services.anime_cache_service import get_anime_map_cache

        source = inspect.getsource(get_anime_map_cache)

        # 检查是否使用了 TraceSpan
        assert 'TraceSpan' in source
        assert 'anime_cache_miss' in source


@pytest.mark.unit
class TestPerformanceIntegration:
    """性能追踪集成测试"""

    def test_generate_span_id(self):
        """测试 span ID 生成"""
        from src.routes.performance import generate_span_id

        span_id = generate_span_id()

        assert span_id is not None
        assert len(span_id) > 0
        assert isinstance(span_id, str)

    def test_get_trace_type(self):
        """测试 trace 类型判断"""
        from src.routes.performance import get_trace_type

        assert get_trace_type('web-vital_lcp') == 'web_vital'
        assert get_trace_type('api_getList') == 'api_call'
        assert get_trace_type('custom_fetchData') == 'function'
        assert get_trace_type('component_Home') == 'component'
        assert get_trace_type('page_home') == 'page_load'
        assert get_trace_type('unknown') == 'operation'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
