import json
import redis
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from config import Config
from models import TaskStatus, ScraperType
import uuid
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )
        self._test_connection()
    
    def _test_connection(self):
        try:
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except redis.ConnectionError as e:
            logger.error(f"Redis连接失败: {e}")
            raise
    
    def create_task(self, urls: List[str], scraper_type: ScraperType, options: Optional[Dict[str, Any]] = None) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task_data = {
            'task_id': task_id,
            'urls': json.dumps(urls),
            'scraper_type': scraper_type.value,
            'status': TaskStatus.PENDING.value,
            'progress': 0,
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'options': json.dumps(options) if options else json.dumps({})
        }
        
        # 存储任务详情
        self.redis_client.hset(f'task:{task_id}', mapping=task_data)
        
        # 添加到任务队列
        self.redis_client.lpush('scrape_queue', task_id)
        
        # 设置过期时间
        self.redis_client.expire(f'task:{task_id}', Config.TASK_EXPIRE_HOURS * 3600)
        
        logger.info(f"创建任务成功: {task_id}")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务详情"""
        task_data = self.redis_client.hgetall(f'task:{task_id}')
        if not task_data:
            return None
        
        # 转换数据类型
        task_data['urls'] = json.loads(task_data['urls'])
        task_data['options'] = json.loads(task_data['options'])
        task_data['progress'] = int(task_data['progress'])
        
        return task_data
    
    def update_task_status(self, task_id: str, status: TaskStatus, progress: Optional[int] = None, error_message: Optional[str] = None):
        """更新任务状态"""
        update_data = {
            'status': status.value,
            'updated_at': datetime.now().isoformat()
        }
        
        if progress is not None:
            update_data['progress'] = progress
        
        if error_message:
            update_data['error_message'] = error_message
        
        if status == TaskStatus.COMPLETED:
            update_data['completed_at'] = datetime.now().isoformat()
        
        self.redis_client.hset(f'task:{task_id}', mapping=update_data)
        logger.info(f"更新任务状态: {task_id} -> {status.value}")
    
    def store_results(self, task_id: str, results: List[Dict[str, Any]]):
        """存储任务结果"""
        result_data = {
            'task_id': task_id,
            'results': json.dumps(results),
            'total_count': len(results),
            'stored_at': datetime.now().isoformat()
        }
        
        # 存储结果
        self.redis_client.hset(f'results:{task_id}', mapping=result_data)
        
        # 更新任务结果数量
        self.redis_client.hset(f'task:{task_id}', mapping={
            'result_count': len(results),
            'progress': 100
        })
        
        # 设置结果过期时间
        self.redis_client.expire(f'results:{task_id}', Config.RESULT_EXPIRE_HOURS * 3600)
        
        logger.info(f"存储结果成功: {task_id}, 共{len(results)}条结果")
    
    def get_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        result_data = self.redis_client.hgetall(f'results:{task_id}')
        if not result_data:
            return None
        
        # 转换数据类型
        result_data['results'] = json.loads(result_data['results'])
        result_data['total_count'] = int(result_data['total_count'])
        
        return result_data
    
    def get_next_task(self) -> Optional[str]:
        """从队列获取下一个任务"""
        task_id = self.redis_client.brpop('scrape_queue', timeout=1)
        if task_id:
            return task_id[1]  # brpop返回(tuple): (queue_name, value)
        return None
    
    def get_queue_length(self) -> int:
        """获取队列长度"""
        return self.redis_client.llen('scrape_queue')
    
    def get_task_stats(self) -> Dict[str, int]:
        """获取任务统计"""
        stats = {
            'pending': 0,
            'processing': 0,
            'completed': 0,
            'failed': 0,
            'queue_length': self.get_queue_length()
        }
        
        # 扫描所有任务
        for key in self.redis_client.scan_iter(match='task:*'):
            status = self.redis_client.hget(key, 'status')
            if status in stats:
                stats[status] += 1
        
        return stats