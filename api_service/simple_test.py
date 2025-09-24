#!/usr/bin/env python3
"""
简单的API测试脚本
"""

import requests
import json
import time
import sys

def test_api():
    """测试API服务"""
    base_url = "http://localhost:5001"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "test-api-key"
    }
    
    print("🚀 开始API测试...")
    
    # 1. 测试健康检查
    print("1️⃣ 测试健康检查...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 2. 测试创建任务
    print("2️⃣ 测试创建任务...")
    payload = {
        "urls": ["https://example.com", "https://httpbin.org/html"],
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
    
    # 3. 测试查询任务状态
    print("3️⃣ 测试查询任务状态...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/tasks/{task_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 任务状态查询成功: {data['status']}")
        else:
            print(f"❌ 任务状态查询失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 任务状态查询异常: {e}")
        return False
    
    # 4. 测试获取统计
    print("4️⃣ 测试获取统计...")
    try:
        response = requests.get(
            f"{base_url}/api/v1/stats",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 统计查询成功: {data}")
        else:
            print(f"❌ 统计查询失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 统计查询异常: {e}")
        return False
    
    print("🎉 所有API测试通过！")
    return True

def wait_for_service(max_wait=60):
    """等待服务启动"""
    print(f"⏳ 等待服务启动 (最多{max_wait}秒)...")
    base_url = "http://localhost:5001"
    
    for i in range(max_wait):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ 服务已启动")
                return True
        except:
            pass
        
        time.sleep(1)
        if i % 10 == 0:
            print(f"已等待{i}秒...")
    
    print("❌ 服务启动超时")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        if not wait_for_service():
            sys.exit(1)
    
    success = test_api()
    sys.exit(0 if success else 1)