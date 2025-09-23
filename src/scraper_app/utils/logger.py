#!/usr/bin/env python3
"""
日志管理
"""

import logging
import sys
from pathlib import Path

from scraper_app.utils.config import Config

def setup_logger(name: str = None, level: str = None) -> logging.Logger:
    """设置日志器"""
    if level is None:
        level = Config.LOG_LEVEL
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # 格式化器
    formatter = logging.Formatter(Config.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)