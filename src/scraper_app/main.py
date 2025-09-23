#!/usr/bin/env python3
"""
主入口文件 - 统一调度所有爬虫
"""

import os
import sys
import argparse
import datetime
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper_app.core.dispatcher import ScraperDispatcher
from scraper_app.utils.config import Config
from scraper_app.utils.logger import setup_logger

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='网络爬虫主程序')
    parser.add_argument('--scraper', '-s', choices=['requests', 'government', 'newspaper', 'readability', 'selenium', 'trafilatura', 'wechat', 'all'], default='requests',
                       help='选择爬虫类型 (默认: requests)')
    parser.add_argument('--input', '-i', default='data/input/webs.txt',
                       help='输入URL文件路径 (默认: data/input/webs.txt)')
    parser.add_argument('--output', '-o', default=None,
                       help='输出目录路径 (默认: data/output/当前时间戳)')
    parser.add_argument('--workers', '-w', type=int, default=5,
                       help='工作线程数 (默认: 5)')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logger()
    
    # 设置输出目录
    if args.output is None:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        args.output = f"data/output/{timestamp}"
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(f"{args.output}/articles", exist_ok=True)
    
    logger.info(f"🕷️  网络爬虫启动")
    logger.info(f"输入文件: {args.input}")
    logger.info(f"输出目录: {args.output}")
    logger.info(f"爬虫类型: {args.scraper}")
    logger.info(f"工作线程: {args.workers}")
    
    # 初始化调度器
    dispatcher = ScraperDispatcher()
    
    # 运行爬虫
    try:
        results = dispatcher.run(args.scraper, args.input, args.output, args.workers)
        logger.info("爬虫执行完成")
        return 0
    except Exception as e:
        logger.error(f"爬虫执行失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())