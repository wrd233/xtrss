#!/usr/bin/env python3
"""
专门测试竞速模式触发
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_race_trigger():
    """测试竞速模式触发"""
    base_url = "http://localhost:5000"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "demo-api-key-123"
    }
    
    print("🎯 专门测试竞速模式触发")
    print("=" * 60)
    
    # 创建更容易失败的任务
    print("🧪 创建高失败率测试任务...")
    
    # 这些URL更容易失败，应该触发竞速模式
    test_urls = [
        "https://httpbin.org/status/404",  # 404错误
        "https://httpbin.org/status/500",  # 500错误
        "https://invalid-domain-xyz123.com", # 无效域名
        "https://httpbin.org/delay/30",    # 超长延迟（会超时）
        "https://httpbin.org/redirect/10", # 过多重定向
        "https://example.com"              # 一个正常的，确保至少有点内容
    ]
    
    payload = {
        "urls": test_urls,
        "scraper_type": "requests"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/scrape",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 202:
            data = response.json()
            task_id = data["task_id"]
            print(f"✅ 任务创建成功: {task_id}")
            
            # 等待并监控状态
            print(f"\n⏳ 监控任务状态变化...")
            
            for i in range(60):  # 最多等待60秒
                try:
                    status_response = requests.get(
                        f"{base_url}/api/v1/tasks/{task_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data["status"]
                        scraper_type = status_data["scraper_type"]
                        progress = status_data["progress"]
                        
                        print(f"⏱️  第{i+1}秒 - 状态: {status}, 类型: {scraper_type}, 进度: {progress}%")
                        
                        # 检查是否转入竞速模式
                        if scraper_type == "race":
                            print(f"🎉 检测到竞速模式触发！任务转入竞速处理")
                            
                            # 等待竞速完成
                            for j in range(i+1, 90):  # 再等待最多30秒
                                time.sleep(1)
                                
                                final_response = requests.get(
                                    f"{base_url}/api/v1/tasks/{task_id}",
                                    headers=headers,
                                    timeout=10
                                )
                                
                                if final_response.status_code == 200:
                                    final_data = final_response.json()
                                    final_status = final_data["status"]
                                    
                                    if final_status == "completed":
                                        print(f"✅ 竞速任务完成！")
                                        
                                        # 获取结果
                                        result_response = requests.get(
                                            f"{base_url}/api/v1/tasks/{task_id}/results",
                                            headers=headers,
                                            timeout=10
                                        )
                                        
                                        if result_response.status_code == 200:
                                            result_data = result_response.json()
                                            print(f"📊 竞速结果:")
                                            print(f"   总结果: {result_data['total_count']}")
                                            print(f"   成功: {result_data['success_count']}")
                                            print(f"   失败: {result_data['failed_count']}")
                                            
                                            # 显示获胜爬虫
                                            if result_data['results']:
                                                winner_scraper = result_data['results'][0].get('scraper_type', 'unknown')
                                                print(f"🏆 获胜爬虫: {winner_scraper}")
                                            
                                            return True
                                        break
                                    elif final_status == "failed":
                                        print(f"❌ 竞速任务失败")
                                        return False
                            break
                        elif status in ["completed", "failed"]:
                            print(f"任务完成，状态: {status}")
                            if status == "completed":
                                print("ℹ️  requests成功完成，未触发竞速模式")
                            return True
                    
                except Exception as e:
                    print(f"状态查询异常: {e}")
                
                time.sleep(1)
            
            print("⏰ 等待超时")
            return False
            
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_simple_race():
    """测试简单竞速模式"""
    print("\n🚀 测试简单竞速模式")
    
    # 创建一个小任务，确保requests会失败
    base_url = "http://localhost:5000"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "demo-api-key-123"
    }
    
    # 手动触发竞速模式 - 通过修改成功率阈值
    test_urls = [
        "https://httpbin.org/status/404",  # 确保失败
        "https://example.com"              # 确保成功
    ]
    
    payload = {
        "urls": test_urls,
        "scraper_type": "requests"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/scrape",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 202:
            data = response.json()
            task_id = data["task_id"]
            print(f"✅ 任务创建成功: {task_id}")
            
            # 这个应该成功率50%，会触发竞速模式（阈值70%）
            print("📊 预期：2个URL，1成功1失败 = 50%成功率 < 70%阈值 = 触发竞速模式")
            
            return task_id
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 创建异常: {e}")
        return None

def main():
    print("🎯 多爬虫竞速模式触发测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试1：简单竞速触发
    task_id = test_simple_race()
    if task_id:
        print(f"\n⏳ 等待任务 {task_id} 完成...")
        time.sleep(30)  # 简单等待
        
        # 检查结果
        base_url = "http://localhost:5000"
        headers = {"X-API-Key": "demo-api-key-123"}
        
        try:
            response = requests.get(f"{base_url}/api/v1/tasks/{task_id}/results", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"📊 结果: 成功{data['success_count']}/{data['total_count']}")
                
                # 检查是否使用了竞速爬虫
                if data['results']:
                    scrapers_used = set(r.get('scraper_type', 'unknown') for r in data['results'])
                    print(f"🔍 使用的爬虫类型: {scrapers_used}")
            else:
                print(f"❌ 结果获取失败: {response.status_code}")
        except Exception as e:
            print(f"❌ 结果获取异常: {e}")
    
    # 测试2：复杂竞速触发
    print(f"\n" + "="*40)
    test_race_trigger()
    
    print("\n" + "=" * 60)
    print("🎉 竞速模式测试完成!")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()