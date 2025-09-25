#!/usr/bin/env python3
"""
简单的并发功能验证脚本
"""

import requests
import json
import time
from datetime import datetime

def simple_test():
    """简单的功能测试"""
    
    print("🧪 简单并发功能测试")
    print("=" * 40)
    
    # API配置
    api_base = "http://localhost:5000"
    api_key = "demo-api-key-123"
    headers = {
        "Content-Type": "application/json", 
        "X-API-Key": api_key
    }
    
    # 简单的测试URL
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html",
        "https://jsonplaceholder.typicode.com/posts/1"
    ]
    
    try:
        # 1. 检查服务健康状态
        print("1. 检查API服务状态...")
        health_resp = requests.get(f"{api_base}/health", timeout=10)
        if health_resp.status_code == 200:
            health_data = health_resp.json()
            print(f"✅ API服务正常: {health_data['status']}")
        else:
            print(f"❌ API服务异常: {health_resp.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务")
        print("请确保Docker容器正在运行:")
        print("docker-compose -f docker-compose.race.yml up -d")
        return False
    
    # 2. 创建爬取任务
    print("\n2. 创建并发爬取任务...")
    task_data = {
        "urls": test_urls,
        "scraper_type": "requests",
        "options": {"timeout": 30}
    }
    
    try:
        response = requests.post(
            f"{api_base}/api/v1/scrape",
            headers=headers,
            json=task_data,
            timeout=10
        )
        
        if response.status_code == 202:
            task_info = response.json()
            task_id = task_info["task_id"]
            print(f"✅ 任务创建成功: {task_id}")
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 创建任务时出错: {str(e)}")
        return False
    
    # 3. 等待任务完成
    print("\n3. 等待任务完成...")
    max_wait = 60
    check_interval = 2
    elapsed = 0
    
    while elapsed < max_wait:
        try:
            status_resp = requests.get(
                f"{api_base}/api/v1/tasks/{task_id}",
                headers=headers,
                timeout=5
            )
            
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data["status"]
                progress = status_data.get("progress", 0)
                
                print(f"\r   状态: {status} (进度: {progress}%)", end="", flush=True)
                
                if status == "completed":
                    print(f"\n✅ 任务完成！")
                    break
                elif status == "failed":
                    print(f"\n❌ 任务失败")
                    return False
            else:
                print(f"\n⚠️  获取状态失败: {status_resp.status_code}")
                
        except Exception as e:
            print(f"\n⚠️  检查状态时出错: {str(e)}")
        
        time.sleep(check_interval)
        elapsed += check_interval
    
    if elapsed >= max_wait:
        print(f"\n⚠️  等待超时")
        return False
    
    # 4. 获取结果
    print("\n4. 获取爬取结果...")
    try:
        result_resp = requests.get(
            f"{api_base}/api/v1/tasks/{task_id}/results",
            headers=headers,
            timeout=10
        )
        
        if result_resp.status_code == 200:
            result_data = result_resp.json()
            results = result_data["results"]
            
            success_count = sum(1 for r in results if r.get("success", False))
            
            print(f"✅ 获取结果成功!")
            print(f"   总URL数: {len(results)}")
            print(f"   成功: {success_count}")
            print(f"   失败: {len(results) - success_count}")
            
            # 显示成功结果
            print(f"\n=== 爬取结果 ===")
            for i, result in enumerate(results):
                status_icon = "✅" if result.get("success", False) else "❌"
                print(f"{status_icon} URL {i+1}: {result['url']}")
                if result.get("success", False):
                    print(f"   标题: {result.get('title', '无标题')}")
                    print(f"   内容长度: {len(result.get('content', ''))} 字符")
                else:
                    print(f"   错误: {result.get('error', '未知错误')}")
                print()
            
            return success_count > 0
        else:
            print(f"❌ 获取结果失败: {result_resp.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 获取结果时出错: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"测试时间: {datetime.now()}")
    success = simple_test()
    
    if success:
        print("🎉 测试通过！并发功能正常工作")
    else:
        print("⚠️ 测试未通过，请检查日志")
        
    print(f"\n查看详细日志:")
    print("docker-compose -f docker-compose.race.yml logs worker_requests")
    print("docker-compose -f docker-compose.race.yml logs api")