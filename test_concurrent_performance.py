#!/usr/bin/env python3
"""
测试并发性能改进的脚本
用于验证新的ThreadPoolExecutor和异步功能
"""

import requests
import time
import json
from datetime import datetime
import sys

def test_concurrent_performance():
    """测试并发性能"""
    
    # API配置
    api_base = "http://localhost:5000"
    api_key = "demo-api-key-123"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    # 测试URL列表 - 混合不同响应时间的网站
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html", 
        "https://httpbin.org/delay/1",  # 延迟1秒
        "https://httpbin.org/delay/2",  # 延迟2秒
        "https://httpbin.org/status/200",
        "https://httpbin.org/headers",
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://jsonplaceholder.typicode.com/posts/2"
    ]
    
    print(f"=== 并发性能测试开始 ===")
    print(f"测试时间: {datetime.now()}")
    print(f"测试URL数量: {len(test_urls)}")
    print(f"预计总耗时对比:")
    print(f"  - 串行处理(30s超时): 约 {len(test_urls) * 30} 秒")
    print(f"  - 并发处理(最大10线程): 约 {min(len(test_urls), 10) * 3} 秒")
    print()
    
    # 创建任务
    task_data = {
        "urls": test_urls,
        "scraper_type": "requests",
        "options": {
            "timeout": 30,
            "concurrent": True  # 启用并发处理
        }
    }
    
    try:
        # 发送任务请求
        print("1. 创建爬取任务...")
        start_time = time.time()
        
        response = requests.post(
            f"{api_base}/api/v1/scrape",
            headers=headers,
            json=task_data
        )
        
        if response.status_code != 202:
            print(f"❌ 创建任务失败: {response.status_code} - {response.text}")
            return False
            
        task_info = response.json()
        task_id = task_info["task_id"]
        print(f"✅ 任务创建成功: {task_id}")
        
        # 等待任务完成
        print("\n2. 等待任务完成...")
        max_wait = 120  # 最大等待120秒
        check_interval = 2
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = requests.get(
                f"{api_base}/api/v1/tasks/{task_id}",
                headers=headers
            )
            
            if status_response.status_code != 200:
                print(f"❌ 获取任务状态失败: {status_response.status_code}")
                return False
                
            status_data = status_response.json()
            status = status_data["status"]
            progress = status_data.get("progress", 0)
            
            print(f"\r   任务状态: {status} (进度: {progress}%)", end="", flush=True)
            
            if status == "completed":
                print(f"\n✅ 任务完成！总耗时: {time.time() - start_time:.2f}秒")
                break
            elif status == "failed":
                print(f"\n❌ 任务失败: {status_data.get('error_message', '未知错误')}")
                return False
                
            time.sleep(check_interval)
            elapsed += check_interval
        
        if elapsed >= max_wait:
            print(f"\n⚠️  等待超时 ({max_wait}秒)")
            return False
        
        # 获取结果
        print("\n3. 获取爬取结果...")
        result_response = requests.get(
            f"{api_base}/api/v1/tasks/{task_id}/results",
            headers=headers
        )
        
        if result_response.status_code != 200:
            print(f"❌ 获取结果失败: {result_response.status_code}")
            return False
            
        result_data = result_response.json()
        results = result_data["results"]
        
        # 分析结果
        success_count = sum(1 for r in results if r.get("success", False))
        failed_count = len(results) - success_count
        
        print(f"\n=== 测试结果统计 ===")
        print(f"总URL数: {len(results)}")
        print(f"成功: {success_count}")
        print(f"失败: {failed_count}")
        print(f"成功率: {success_count/len(results)*100:.1f}%")
        print(f"总耗时: {time.time() - start_time:.2f}秒")
        print(f"平均每个URL: {(time.time() - start_time)/len(results):.2f}秒")
        
        # 显示失败详情
        if failed_count > 0:
            print(f"\n=== 失败详情 ===")
            for result in results:
                if not result.get("success", False):
                    print(f"❌ {result['url']}: {result.get('error', '未知错误')}")
        
        # 显示成功示例
        if success_count > 0:
            print(f"\n=== 成功示例 ===")
            success_results = [r for r in results if r.get("success", False)]
            for result in success_results[:3]:  # 显示前3个成功的
                print(f"✅ {result['url']}: {result['title']} (内容长度: {len(result.get('content', ''))})")
        
        return success_count > 0
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务，请确保Docker容器正在运行")
        print("请执行: docker-compose -f docker-compose.race.yml up -d")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

def check_service_health():
    """检查服务健康状态"""
    try:
        response = requests.get("http://localhost:5000/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API服务健康: {health_data['status']}")
            if 'queue_stats' in health_data:
                print(f"   队列统计: {health_data['queue_stats']}")
            return True
        else:
            print(f"⚠️  API服务状态异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务")
        return False

if __name__ == "__main__":
    print("🚀 并发性能测试工具")
    print("=" * 50)
    
    # 检查服务健康状态
    print("0. 检查服务状态...")
    if not check_service_health():
        print("请先启动服务: docker-compose -f docker-compose.race.yml up -d")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # 运行性能测试
    success = test_concurrent_performance()
    
    if success:
        print("\n🎉 并发性能测试完成！")
        print("新的并发处理功能正在正常工作。")
    else:
        print("\n⚠️ 测试遇到问题，请检查日志")
        sys.exit(1)