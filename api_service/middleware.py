import time
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
from collections import defaultdict, deque
from config import Config
from models import ErrorResponse
import logging

logger = logging.getLogger(__name__)

# 简单的IP限流实现
class RateLimiter:
    def __init__(self, max_requests=60, window_minutes=1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = defaultdict(deque)
    
    def is_allowed(self, ip):
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # 清理过期的请求记录
        while self.requests[ip] and self.requests[ip][0] < window_start:
            self.requests[ip].popleft()
        
        # 检查是否超过限制
        if len(self.requests[ip]) >= self.max_requests:
            return False
        
        # 记录当前请求
        self.requests[ip].append(now)
        return True
    
    def get_retry_after(self, ip):
        if not self.requests[ip]:
            return 0
        oldest_request = self.requests[ip][0]
        retry_after = (oldest_request + timedelta(minutes=self.window_minutes) - datetime.now()).seconds
        return max(0, retry_after)

# 创建限流器实例
rate_limiter = RateLimiter(max_requests=Config.RATE_LIMIT_PER_MINUTE)

def setup_middleware(app):
    """设置应用中间件"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
        
        # 记录请求日志
        logger.info(f"{request.method} {request.path} - {request.remote_addr}")
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
            
            logger.info(f"{request.method} {request.path} - {response.status_code} - {elapsed:.3f}s")
        
        return response

def require_api_key(f):
    """API Key验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 开发环境跳过验证
        if Config.FLASK_ENV == 'development':
            return f(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify(ErrorResponse(
                error="Unauthorized",
                message="缺少API Key"
            ).dict()), 401
        
        if api_key != Config.API_KEY:
            logger.warning(f"无效的API Key尝试: {api_key} from {request.remote_addr}")
            return jsonify(ErrorResponse(
                error="Unauthorized", 
                message="无效的API Key"
            ).dict()), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def rate_limit(f):
    """速率限制装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if Config.FLASK_ENV == 'development':
            return f(*args, **kwargs)
        
        ip = request.remote_addr
        if not rate_limiter.is_allowed(ip):
            retry_after = rate_limiter.get_retry_after(ip)
            logger.warning(f"IP {ip} 触发限流")
            
            response = jsonify(ErrorResponse(
                error="RateLimitExceeded",
                message="请求过于频繁，请稍后再试",
                details={"retry_after": retry_after}
            ).dict()), 429
            
            response[0].headers['Retry-After'] = str(retry_after)
            return response
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_json(f):
    """JSON验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                return jsonify(ErrorResponse(
                    error="BadRequest",
                    message="请求必须是JSON格式"
                ).dict()), 400
            
            if not request.json:
                return jsonify(ErrorResponse(
                    error="BadRequest",
                    message="请求体不能为空"
                ).dict()), 400
        
        return f(*args, **kwargs)
    
    return decorated_function