import json
import redis
import logging
from typing import Optional, Dict, List, Any
from config import Config, TaskStatus

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
    
    def get_next_task(self) -> Optional[str]:
        """从队列获取下一个任务"""
        task_id = self.redis_client.brpop('scrape_queue', timeout=Config.POLL_INTERVAL)
        if task_id:
            return task_id[1]  # brpop返回(tuple): (queue_name, value)
        return None
    
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
        import datetime
        update_data = {
            'status': status.value,
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        if progress is not None:
            update_data['progress'] = progress
        
        if error_message:
            update_data['error_message'] = error_message
        
        if status == TaskStatus.COMPLETED:
            update_data['completed_at'] = datetime.datetime.now().isoformat()
        
        self.redis_client.hset(f'task:{task_id}', mapping=update_data)
        logger.info(f"更新任务状态: {task_id} -> {status.value}")
    
    def store_results(self, task_id: str, results: List[Dict[str, Any]]):
        """存储任务结果"""
        import datetime
        result_data = {
            'task_id': task_id,
            'results': json.dumps(results),
            'total_count': len(results),
            'stored_at': datetime.datetime.now().isoformat()
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