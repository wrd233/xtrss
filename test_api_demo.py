#!/usr/bin/env python3
"""
API测试演示脚本 - 展示如何使用爬虫API服务
"""

import requests
import json
import time
import sys
from datetime import datetime

class ScraperAPITester:
    def __init__(self, base_url="http://localhost:5000", api_key="demo-api-key-123"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def health_check(self):
        """健康检查"""
        print("🔍 健康检查...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 服务健康")
                print(f"   Redis连接: {data['redis_connected']}")
                print(f"   队列状态: {data['queue_stats']}")
                print(f"   时间戳: {data['timestamp']}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def create_task(self, urls, scraper_type="requests"):
        """创建爬取任务"""
        print(f"\n📝 创建爬取任务 ({len(urls)}个URL)...")
        
        payload = {
            "urls": urls,
            "scraper_type": scraper_type,
            "options": {}
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/scrape",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 202:
                data = response.json()
                task_id = data["task_id"]
                print(f"✅ 任务创建成功!")
                print(f"   任务ID: {task_id}")
                print(f"   初始状态: {data['status']}")
                print(f"   创建时间: {data['created_at']}")
                print(f"   消息: {data['message']}")
                return task_id
            else:
                print(f"❌ 任务创建失败: {response.status_code}")
                print(f"响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 任务创建异常: {e}")
            return None
    
    def get_task_status(self, task_id):
        """获取任务状态"""
        print(f"\n📊 查询任务状态: {task_id}")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tasks/{task_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 状态查询成功")
                print(f"   状态: {data['status']}")
                print(f"   爬虫类型: {data['scraper_type']}")
                print(f"   URL数量: {len(data['urls'])}")
                print(f"   进度: {data['progress']}%")
                print(f"   创建时间: {data['created_at']}")
                
                if data.get('completed_at'):
                    print(f"   完成时间: {data['completed_at']}")
                if data.get('result_count') is not None:
                    print(f"   结果数量: {data['result_count']}")
                if data.get('error_message'):
                    print(f"   错误信息: {data['error_message']}")
                    
                return data['status']
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 状态查询异常: {e}")
            return None
    
    def get_task_results(self, task_id):
        """获取任务结果"""
        print(f"\n📋 获取任务结果: {task_id}")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tasks/{task_id}/results",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 结果获取成功")
                print(f"   任务状态: {data['status']}")
                print(f"   结果总数: {data['total_count']}")
                print(f"   成功数量: {data['success_count']}")
                print(f"   失败数量: {data['failed_count']}")
                
                # 显示部分结果摘要
                results = data.get('results', [])
                if results:
                    print(f"\n📄 结果摘要:")
                    for i, result in enumerate(results[:3]):  # 显示前3个结果
                        print(f"\n   结果 {i+1}:")
                        print(f"     URL: {result['url']}")
                        print(f"     成功: {result['success']}")
                        if result['success']:
                            print(f"     标题: {result['title']}")
                            content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                            print(f"     内容预览: {content_preview}")
                        else:
                            print(f"     错误: {result['error']}")
                    
                    if len(results) > 3:
                        print(f"\n   ... 还有 {len(results) - 3} 个结果")
                
                return data
            elif response.status_code == 425:
                print(f"⏳ 任务尚未完成 (状态码: 425)")
                return None
            else:
                print(f"❌ 结果获取失败: {response.status_code}")
                print(f"响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 结果获取异常: {e}")
            return None
    
    def get_stats(self):
        """获取系统统计"""
        print(f"\n📈 获取系统统计...")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/stats",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 统计获取成功")
                print(f"   待处理: {data['pending']} 个任务")
                print(f"   处理中: {data['processing']} 个任务")
                print(f"   已完成: {data['completed']} 个任务")
                print(f"   失败: {data['failed']} 个任务")
                print(f"   队列长度: {data['queue_length']}")
                return data
            else:
                print(f"❌ 统计获取失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 统计获取异常: {e}")
            return None
    
    def wait_for_completion(self, task_id, max_wait=60, check_interval=2):
        """等待任务完成"""
        print(f"\n⏳ 等待任务完成 (最多{max_wait}秒)...")
        
        for i in range(0, max_wait, check_interval):
            status = self.get_task_status(task_id)
            if status == "completed":
                print(f"✅ 任务已完成!")
                return True
            elif status == "failed":
                print(f"❌ 任务失败!")
                return False
            elif status is None:
                print(f"❌ 无法获取任务状态")
                return False
            
            print(f"   等待中... ({i+check_interval}/{max_wait}秒)")
            time.sleep(check_interval)
        
        print(f"⏰ 等待超时!")
        return False

def main():
    """主测试函数"""
    print("🚀 爬虫API测试演示")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 创建测试实例
    tester = ScraperAPITester()
    
    # 1. 健康检查
    if not tester.health_check():
        print("\n❌ 服务不可用，请确保Docker容器已启动")
        print("尝试运行: docker-compose -f docker-compose.prod.yml up -d")
        return False
    
    # 2. 获取初始统计
    tester.get_stats()
    
    # 3. 创建测试任务
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://httpbin.org/json"
    ]
    
    task_id = tester.create_task(test_urls)
    if not task_id:
        return False
    
    # 4. 等待任务完成
    if not tester.wait_for_completion(task_id, max_wait=30):
        return False
    
    # 5. 获取最终结果
    results = tester.get_task_results(task_id)
    if not results:
        return False
    
    # 6. 最终统计
    tester.get_stats()
    
    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)