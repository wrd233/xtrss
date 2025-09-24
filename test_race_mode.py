#!/usr/bin/env python3
"""
多爬虫竞速模式测试脚本
"""

import requests
import json
import time
import sys
from datetime import datetime

class RaceModeTester:
    def __init__(self, base_url="http://localhost:5000", api_key="demo-api-key-123"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def create_problematic_task(self):
        """创建一个可能失败的测试任务"""
        print("🧪 创建测试任务（包含可能失败的URL）...")
        
        # 包含一些可能失败的URL，测试竞速模式
        test_urls = [
            "https://example.com",  # 正常URL
            "https://httpbin.org/status/404",  # 404错误
            "https://httpbin.org/delay/10",    # 延迟响应
            "https://httpbin.org/html",        # 正常HTML
            "https://invalid-domain-12345.com" # 无效域名
        ]
        
        payload = {
            "urls": test_urls,
            "scraper_type": "requests"  # 先用requests尝试
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
                print(f"✅ 任务创建成功: {task_id}")
                return task_id
            else:
                print(f"❌ 任务创建失败: {response.status_code}")
                print(f"响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 任务创建异常: {e}")
            return None
    
    def wait_and_check_result(self, task_id, max_wait=60):
        """等待并检查结果"""
        print(f"\n⏳ 等待任务完成: {task_id}")
        
        for i in range(0, max_wait, 2):
            try:
                # 检查状态
                response = requests.get(
                    f"{self.base_url}/api/v1/tasks/{task_id}",
                    headers=self.headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data["status"]
                    progress = data["progress"]
                    scraper_type = data["scraper_type"]
                    
                    print(f"⏱️  第{i+2}秒 - 状态: {status}, 类型: {scraper_type}, 进度: {progress}%")
                    
                    if status == "completed":
                        print(f"✅ 任务完成!")
                        return self.get_final_results(task_id)
                    elif status == "failed":
                        print(f"❌ 任务失败: {data.get('error_message', '未知错误')}")
                        return False
                else:
                    print(f"❌ 状态查询失败: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ 状态查询异常: {e}")
                return False
            
            time.sleep(2)
        
        print(f"⏰ 等待超时!")
        return False
    
    def get_final_results(self, task_id):
        """获取最终结果"""
        print(f"\n📋 获取任务结果: {task_id}")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/tasks/{task_id}/results",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data["results"]
                
                print(f"📊 结果统计:")
                print(f"   总结果数: {data['total_count']}")
                print(f"   成功数量: {data['success_count']}")
                print(f"   失败数量: {data['failed_count']}")
                
                # 按爬虫类型统计
                scraper_stats = {}
                for result in results:
                    scraper = result.get('scraper_type', 'unknown')
                    if scraper not in scraper_stats:
                        scraper_stats[scraper] = {'success': 0, 'failed': 0}
                    
                    if result.get('success', False):
                        scraper_stats[scraper]['success'] += 1
                    else:
                        scraper_stats[scraper]['failed'] += 1
                
                print(f"\n🔍 按爬虫类型统计:")
                for scraper, stats in scraper_stats.items():
                    total = stats['success'] + stats['failed']
                    success_rate = stats['success'] / total * 100 if total > 0 else 0
                    print(f"   {scraper}: {stats['success']}/{total} 成功 ({success_rate:.1f}%)")
                
                # 显示几个成功结果
                success_results = [r for r in results if r.get('success', False)]
                if success_results:
                    print(f"\n✨ 成功结果示例:")
                    for i, result in enumerate(success_results[:2]):
                        print(f"\n   结果 {i+1}:")
                        print(f"     URL: {result['url']}")
                        print(f"     爬虫: {result.get('scraper_type', 'unknown')}")
                        print(f"     标题: {result['title']}")
                        print(f"     内容长度: {len(result['content'])} 字符")
                
                return True
                
            else:
                print(f"❌ 结果获取失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 结果获取异常: {e}")
            return False
    
    def test_race_mode_directly(self):
        """直接测试竞速模式"""
        print("\n🏁 直接测试竞速模式...")
        
        # 创建一个竞速模式任务
        test_urls = [
            "https://example.com",
            "https://httpbin.org/html",
            "https://httpbin.org/json"
        ]
        
        payload = {
            "urls": test_urls,
            "scraper_type": "race"  # 直接使用竞速模式
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
                print(f"✅ 竞速任务创建成功: {task_id}")
                return task_id
            else:
                print(f"❌ 竞速任务创建失败: {response.status_code}")
                print(f"响应: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 竞速任务创建异常: {e}")
            return None
    
    def get_system_stats(self):
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
                print(f"📊 系统状态:")
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

def main():
    print("🚀 多爬虫竞速模式测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tester = RaceModeTester()
    
    # 1. 健康检查
    print("🔍 健康检查...")
    try:
        response = requests.get("http://localhost:5000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务健康 - Redis连接: {data['redis_connected']}")
        else:
            print(f"❌ 健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 2. 获取初始统计
    tester.get_system_stats()
    
    # 3. 测试正常流程（requests -> 竞速模式）
    print(f"\n🔄 测试容错流程（requests -> 竞速模式）")
    task_id = tester.create_problematic_task()
    if not task_id:
        return False
    
    success = tester.wait_and_check_result(task_id)
    if not success:
        print("❌ 容错流程测试失败")
        return False
    
    # 4. 测试直接竞速模式
    print(f"\n🚀 测试直接竞速模式")
    race_task_id = tester.test_race_mode_directly()
    if race_task_id:
        tester.wait_and_check_result(race_task_id)
    
    # 5. 最终统计
    tester.get_system_stats()
    
    print("\n" + "=" * 60)
    print("🎉 测试完成!")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)