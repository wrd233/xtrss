from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging
import os

from config import Config
from models import (
    ScrapeRequest, TaskResponse, TaskStatusResponse, 
    TaskResultResponse, ErrorResponse, TaskStatus, ScraperType
)
from redis_client import RedisClient
from middleware import setup_middleware, require_api_key, rate_limit

# 设置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 启用CORS
CORS(app)

# 设置中间件
setup_middleware(app)

# 初始化Redis客户端
try:
    redis_client = RedisClient()
    logger.info("Redis客户端初始化成功")
except Exception as e:
    logger.error(f"Redis客户端初始化失败: {e}")
    redis_client = None

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'redis_connected': redis_client is not None
    }
    
    if redis_client:
        try:
            stats = redis_client.get_task_stats()
            health_status['queue_stats'] = stats
        except Exception as e:
            health_status['redis_error'] = str(e)
            health_status['status'] = 'degraded'
    
    return jsonify(health_status), 200

@app.route('/api/v1/scrape', methods=['POST'])
@require_api_key
def create_scrape_task():
    """创建爬取任务"""
    try:
        if not redis_client:
            return jsonify(ErrorResponse(
                error="ServiceUnavailable",
                message="Redis服务不可用"
            ).model_dump()), 503
        
        # 验证请求数据
        try:
            scrape_request = ScrapeRequest(**request.json)
        except Exception as e:
            return jsonify(ErrorResponse(
                error="BadRequest",
                message="请求数据验证失败",
                details={"validation_error": str(e)}
            ).model_dump()), 400
        
        # 创建任务
        task_id = redis_client.create_task(
            urls=scrape_request.urls,
            scraper_type=scrape_request.scraper_type,
            options=scrape_request.options
        )
        
        response = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            message="任务创建成功，正在排队处理"
        )
        
        logger.info(f"创建爬取任务: {task_id}, URLs: {len(scrape_request.urls)}, 类型: {scrape_request.scraper_type.value}")
        return jsonify(response.model_dump()), 202
        
    except Exception as e:
        logger.error(f"创建任务失败: {e}")
        return jsonify(ErrorResponse(
            error="InternalServerError",
            message="创建任务失败",
            details={"error": str(e)}
        ).model_dump()), 500

@app.route('/api/v1/tasks/<task_id>', methods=['GET'])
@require_api_key
def get_task_status(task_id):
    """获取任务状态"""
    try:
        if not redis_client:
            return jsonify(ErrorResponse(
                error="ServiceUnavailable",
                message="Redis服务不可用"
            ).model_dump()), 503
        
        task_data = redis_client.get_task(task_id)
        if not task_data:
            return jsonify(ErrorResponse(
                error="NotFound",
                message="任务不存在"
            ).model_dump()), 404
        
        response = TaskStatusResponse(
            task_id=task_data['task_id'],
            status=TaskStatus(task_data['status']),
            scraper_type=ScraperType(task_data['scraper_type']),
            urls=task_data['urls'],
            progress=task_data['progress'],
            created_at=datetime.fromisoformat(task_data['created_at']),
            updated_at=datetime.fromisoformat(task_data['updated_at']),
            completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data.get('completed_at') else None,
            result_count=int(task_data.get('result_count', 0)) if task_data.get('result_count') else None,
            error_message=task_data.get('error_message')
        )
        
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        return jsonify(ErrorResponse(
            error="InternalServerError",
            message="获取任务状态失败",
            details={"error": str(e)}
        ).model_dump()), 500

@app.route('/api/v1/tasks/<task_id>/results', methods=['GET'])
@require_api_key
def get_task_results(task_id):
    """获取任务结果"""
    try:
        if not redis_client:
            return jsonify(ErrorResponse(
                error="ServiceUnavailable",
                message="Redis服务不可用"
            ).model_dump()), 503
        
        # 获取任务信息
        task_data = redis_client.get_task(task_id)
        if not task_data:
            return jsonify(ErrorResponse(
                error="NotFound",
                message="任务不存在"
            ).model_dump()), 404
        
        # 检查任务是否完成
        if TaskStatus(task_data['status']) != TaskStatus.COMPLETED:
            return jsonify(ErrorResponse(
                error="NotReady",
                message="任务尚未完成",
                details={"status": task_data['status']}
            ).model_dump()), 425
        
        # 获取结果
        result_data = redis_client.get_results(task_id)
        if not result_data:
            return jsonify(ErrorResponse(
                error="NotFound",
                message="任务结果不存在或已过期"
            ).model_dump()), 404
        
        response = TaskResultResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            results=result_data['results'],
            total_count=result_data['total_count'],
            success_count=result_data['total_count'],  # 简化处理
            failed_count=0,
            created_at=datetime.fromisoformat(task_data['created_at']),
            completed_at=datetime.fromisoformat(task_data['completed_at']) if task_data.get('completed_at') else None
        )
        
        return jsonify(response.model_dump()), 200
        
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        return jsonify(ErrorResponse(
            error="InternalServerError",
            message="获取任务结果失败",
            details={"error": str(e)}
        ).model_dump()), 500

@app.route('/api/v1/stats', methods=['GET'])
@require_api_key
def get_stats():
    """获取系统统计信息"""
    try:
        if not redis_client:
            return jsonify(ErrorResponse(
                error="ServiceUnavailable",
                message="Redis服务不可用"
            ).model_dump()), 503
        
        stats = redis_client.get_task_stats()
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify(ErrorResponse(
            error="InternalServerError",
            message="获取统计信息失败",
            details={"error": str(e)}
        ).model_dump()), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify(ErrorResponse(
        error="NotFound",
        message="接口不存在"
    ).model_dump()), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify(ErrorResponse(
        error="MethodNotAllowed",
        message="HTTP方法不允许"
    ).model_dump()), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify(ErrorResponse(
        error="InternalServerError",
        message="服务器内部错误"
    ).dict()), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = Config.FLASK_ENV == 'development'
    
    logger.info(f"启动Flask应用，端口: {port}, 调试模式: {debug}")
    app.run(host='0.0.0.0', port=port, debug=debug)