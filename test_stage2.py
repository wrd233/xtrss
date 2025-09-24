#!/usr/bin/env python3
"""
阶段2集成测试脚本 - 测试API + Worker完整流程
"""

import requests
import json
import time
import sys

def test_stage2():
    """测试阶段2完整流程"""
    base_url = "http://localhost:5002"  # 阶段2 API端口
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "stage2-api-key"
    }
    
    print("🚀 阶段2集成测试开始...")
    print("=" * 50)
    
    # 1. 测试健康检查
    print("1️⃣ 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过")
            print(f"   Redis连接: {data['redis_connected']}")
            print(f"   队列状态: {data['queue_stats']}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 2. 创建爬取任务
    print("\n2️⃣ 创建爬取任务...")
    test_urls = [
        "https://example.com",
        "https://httpbin.org/html"
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
        else:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 任务创建异常: {e}")
        return False
    
    # 3. 轮询任务状态
    print(f"\n3️⃣ 轮询任务状态: {task_id}")
    max_retries = 30  # 最多等待30秒
    retry_interval = 1
    
    for i in range(max_retries):
        try:
            response = requests.get(
                f"{base_url}/api/v1/tasks/{task_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data["status"]
                progress = status_data["progress"]
                
                print(f"⏳ 第{i+1}秒 - 状态: {status}, 进度: {progress}%")
                
                if status == "completed":
                    print(f"✅ 任务完成！")
                    break
                elif status == "failed":
                    print(f"❌ 任务失败: {status_data.get('error_message', '未知错误')}")
                    return False
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 状态查询异常: {e}")
            return False
        
        time.sleep(retry_interval)
    else:
        print("⚠️  任务超时未完成")
        return False
    
    # 4. 获取任务结果
    print("\n4️⃣ 获取任务结果...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/tasks/{task_id}/results",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result_data = response.json()
            results = result_data["results"]
            total_count = result_data["total_count"]
            
            print(f"✅ 获取结果成功: {total_count}条结果")
            
            # 显示结果摘要
            for i, result in enumerate(results[:2]):  # 只显示前2个结果
                print(f"\n📄 结果 {i+1}:")
                print(f"   URL: {result['url']}")
                print(f"   成功: {result['success']}")
                if result['success']:
                    print(f"   标题: {result['title']}")
                    print(f"   内容长度: {len(result['content'])} 字符")
                else:
                    print(f"   错误: {result['error']}")
            
            if len(results) > 2:
                print(f"\n   ... 还有 {len(results) - 2} 个结果")
                
        else:
            print(f"❌ 获取结果失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 获取结果异常: {e}")
        return False
    
    # 5. 最终验证
    print("\n5️⃣ 最终验证...")
    try:
        response = requests.get(f"{base_url}/api/v1/stats", headers=headers, timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"📊 最终统计: {stats}")
            
            if stats.get('completed', 0) > 0:
                print("✅ 验证通过 - 有完成的任务")
            else:
                print("⚠️  验证警告 - 没有完成的任务")
        else:
            print(f"❌ 统计查询失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 最终验证异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 阶段2集成测试完成！")
    return True

def wait_for_service(max_wait=60):
    """等待服务启动"""
    print(f"⏳ 等待阶段2服务启动 (最多{max_wait}秒)...")
    base_url = "http://localhost:5002"
    
    for i in range(max_wait):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ 阶段2服务已启动")
                return True
        except:
            pass
        
        time.sleep(1)
        if i % 10 == 0:
            print(f"已等待{i}秒...")
    
    print("❌ 阶段2服务启动超时")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        if not wait_for_service():
            sys.exit(1)
    
    success = test_stage2()
    sys.exit(0 if success else 1)