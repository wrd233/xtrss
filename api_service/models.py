from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class ScraperType(str, Enum):
    REQUESTS = "requests"
    NEWSPAPER = "newspaper"
    READABILITY = "readability"
    TRAFILATURA = "trafilatura"
    RACE = "race"  # 竞速模式 - 多个爬虫同时尝试

class ScrapeRequest(BaseModel):
    urls: List[str] = Field(..., min_items=1, max_items=100, description="要爬取的URL列表")
    scraper_type: ScraperType = Field(default=ScraperType.REQUESTS, description="爬虫类型")
    options: Optional[Dict[str, Any]] = Field(default=None, description="爬虫选项配置")
    
    @validator('urls')
    def validate_urls(cls, v):
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError(f'Invalid URL: {url}')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TaskResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    message: str = Field(..., description="响应消息")

class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    scraper_type: ScraperType = Field(..., description="爬虫类型")
    urls: List[str] = Field(..., description="URL列表")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    result_count: Optional[int] = Field(default=None, description="结果数量")
    error_message: Optional[str] = Field(default=None, description="错误信息")

class TaskResultResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="爬取结果")
    total_count: int = Field(default=0, description="结果总数")
    success_count: int = Field(default=0, description="成功数量")
    failed_count: int = Field(default=0, description="失败数量")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="详细错误信息")