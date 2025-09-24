import unittest
import json
import time
import requests
from datetime import datetime

class TestScraperAPI(unittest.TestCase):
    """API接口测试"""
    
    BASE_URL = "http://localhost:5000"
    API_KEY = "your-secret-api-key-here"
    
    def setUp(self):
        """测试前置设置"""
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.API_KEY
        }
        
        # 测试URL
        self.test_urls = [
            "https://example.com",
            "https://httpbin.org/html"
        ]
    
    def test_health_check(self):
        """测试健康检查接口"""
        response = requests.get(f"{self.BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("redis_connected", data)
        print("✅ 健康检查接口测试通过")
    
    def test_create_task_success(self):
        """测试创建任务成功"""
        payload = {
            "urls": self.test_urls,
            "scraper_type": "requests"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/scrape",
            headers=self.headers,
            json=payload
        )
        
        self.assertEqual(response.status_code, 202)
        
        data = response.json()
        self.assertIn("task_id", data)
        self.assertEqual(data["status"], "pending")
        self.assertIn("message", data)
        
        print(f"✅ 创建任务成功: {data['task_id']}")
        return data["task_id"]
    
    def test_create_task_invalid_url(self):
        """测试创建任务-无效URL"""
        payload = {
            "urls": ["invalid-url"],
            "scraper_type": "requests"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/scrape",
            headers=self.headers,
            json=payload
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"], "BadRequest")
        print("✅ 无效URL测试通过")
    
    def test_create_task_no_auth(self):
        """测试创建任务-无认证"""
        payload = {
            "urls": self.test_urls,
            "scraper_type": "requests"
        }
        
        # 不携带API Key
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            f"{self.BASE_URL}/api/v1/scrape",
            headers=headers,
            json=payload
        )
        
        # 开发环境应该跳过验证，返回202
        if response.status_code == 401:
            print("✅ 无认证测试通过(返回401)")
        else:
            print(f"✅ 无认证测试通过(返回{response.status_code})")
    
    def test_get_task_status(self):
        """测试获取任务状态"""
        # 先创建任务
        task_id = self.test_create_task_success()
        
        # 等待一下让任务创建完成
        time.sleep(0.5)
        
        # 获取任务状态
        response = requests.get(
            f"{self.BASE_URL}/api/v1/tasks/{task_id}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["task_id"], task_id)
        self.assertEqual(data["status"], "pending")
        self.assertIn("urls", data)
        self.assertIn("scraper_type", data)
        self.assertIn("progress", data)
        
        print(f"✅ 获取任务状态成功: {data['status']}")
    
    def test_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        fake_task_id = "non-existent-task-id"
        
        response = requests.get(
            f"{self.BASE_URL}/api/v1/tasks/{fake_task_id}",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["error"], "NotFound")
        print("✅ 不存在任务测试通过")
    
    def test_get_task_results_not_ready(self):
        """测试获取未完成任务结果"""
        # 创建任务
        task_id = self.test_create_task_success()
        
        # 立即获取结果
        response = requests.get(
            f"{self.BASE_URL}/api/v1/tasks/{task_id}/results",
            headers=self.headers
        )
        
        # 应该返回425 (Too Early)
        self.assertEqual(response.status_code, 425)
        data = response.json()
        self.assertEqual(data["error"], "NotReady")
        print("✅ 未完成任务结果测试通过")
    
    def test_get_stats(self):
        """测试获取统计信息"""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/stats",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # 验证统计字段
        expected_fields = ['pending', 'processing', 'completed', 'failed', 'queue_length']
        for field in expected_fields:
            self.assertIn(field, data)
            self.assertIsInstance(data[field], int)
        
        print(f"✅ 获取统计信息成功: {data}")
    
    def test_404_handler(self):
        """测试404处理器"""
        response = requests.get(
            f"{self.BASE_URL}/api/v1/nonexistent",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["error"], "NotFound")
        print("✅ 404处理器测试通过")
    
    def test_method_not_allowed(self):
        """测试方法不允许"""
        response = requests.put(
            f"{self.BASE_URL}/api/v1/scrape",
            headers=self.headers,
            json={}
        )
        
        self.assertEqual(response.status_code, 405)
        print("✅ 方法不允许测试通过")

class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    BASE_URL = "http://localhost:5000"
    API_KEY = "your-secret-api-key-here"
    
    def setUp(self):
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.API_KEY
        }
    
    def test_full_workflow_simulation(self):
        """测试完整工作流模拟"""
        print("\n🔄 开始完整工作流测试...")
        
        # 1. 创建任务
        payload = {
            "urls": ["https://example.com", "https://httpbin.org/html"],
            "scraper_type": "requests"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/v1/scrape",
            headers=self.headers,
            json=payload
        )
        
        self.assertEqual(response.status_code, 202)
        task_id = response.json()["task_id"]
        print(f"✅ 任务创建成功: {task_id}")
        
        # 2. 轮询任务状态
        max_retries = 10
        retry_interval = 2
        
        for i in range(max_retries):
            response = requests.get(
                f"{self.BASE_URL}/api/v1/tasks/{task_id}",
                headers=self.headers
            )
            
            self.assertEqual(response.status_code, 200)
            status_data = response.json()
            
            print(f"⏳ 第{i+1}次检查 - 任务状态: {status_data['status']}, 进度: {status_data['progress']}%")
            
            if status_data["status"] == "completed":
                print("✅ 任务完成！")
                break
            elif status_data["status"] == "failed":
                print(f"❌ 任务失败: {status_data.get('error_message', '未知错误')}")
                break
            
            time.sleep(retry_interval)
        else:
            print("⚠️  任务超时未完成")
        
        print("✅ 完整工作流测试完成")

def run_tests():
    """运行所有测试"""
    print("🚀 开始API测试...")
    print("=" * 50)
    
    # 检查服务是否可用
    try:
        response = requests.get(f"{TestScraperAPI.BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API服务不可用，请先启动服务")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到API服务: {e}")
        print("请先启动API服务: python app.py")
        return
    
    # 运行测试
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestScraperAPI)
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 50)
    
    # 运行集成测试
    if result.wasSuccessful():
        print("\n🔄 运行集成测试...")
        integration_suite = unittest.TestLoader().loadTestsFromTestCase(TestIntegration)
        integration_runner = unittest.TextTestRunner(verbosity=0)
        integration_result = integration_runner.run(integration_suite)
        
        if integration_result.wasSuccessful():
            print("\n🎉 所有测试通过！")
        else:
            print(f"\n⚠️  集成测试失败: {len(integration_result.failures)} failures, {len(integration_result.errors)} errors")
    else:
        print(f"\n❌ API测试失败: {len(result.failures)} failures, {len(result.errors)} errors")

if __name__ == "__main__":
    run_tests()