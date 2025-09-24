import os
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class Config:
    # Redis配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # Worker配置
    WORKER_TYPE = os.getenv('WORKER_TYPE', 'all')  # all, requests, selenium, etc.
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 3))
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', 5))  # 秒
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # 支持的爬虫类型
    SUPPORTED_SCRAPERS = [
        'requests', 'government', 'newspaper', 
        'readability', 'selenium', 'trafilatura', 'wechat'
    ]
    
    # 结果配置
    RESULT_EXPIRE_HOURS = 24
    
    # 错误重试配置
    MAX_RETRY_COUNT = 3
    RETRY_DELAY_SECONDS = 30