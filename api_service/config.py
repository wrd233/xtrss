import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Redis配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # API配置
    API_KEY = os.getenv('API_KEY', 'your-secret-api-key-here')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # 限流配置
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    
    # 任务配置
    TASK_EXPIRE_HOURS = 24
    RESULT_EXPIRE_HOURS = 24
    
    # 支持的爬虫类型（包含竞速模式）
    SUPPORTED_SCRAPERS = [
        'requests', 'newspaper', 'readability', 'trafilatura', 'race'
    ]
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB