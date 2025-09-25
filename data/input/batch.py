import requests
import json
import time
import threading
from threading import Lock
from queue import Queue
import argparse
from typing import List, Dict, Any
import os

class URLScraper:
    def __init__(self, api_url: str = "http://localhost:5000", api_key: str = "demo-api-key-123"):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-API-Key": self.api_key})
        
        # 存储结果
        self.results = []
        self.results_lock = Lock()
        
        # 任务队列
        self.task_queue = Queue()
        self.completed_tasks = set()
        
    def check_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = self.session.get(f"{self.api_url}/health", timeout=10)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def submit_scraping_task(self, urls: List[str]) -> str:
        """提交爬取任务"""
        data = {
            "urls": urls,
            "scraper_type": "requests"
        }
        
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/scrape",
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get("task_id")
        except requests.exceptions.RequestException as e:
            print(f"提交任务失败: {e}")
            return None
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/tasks/{task_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取任务状态失败 {task_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_task_results(self, task_id: str) -> Dict[str, Any]:
        """获取任务结果"""
        try:
            response = self.session.get(
                f"{self.api_url}/api/v1/tasks/{task_id}/results",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取任务结果失败 {task_id}: {e}")
            return {"error": str(e)}
    
    def process_single_url(self, url: str, task_id: str):
        """处理单个URL的任务状态轮询"""
        max_retries = 60  # 最大重试次数（5分钟）
        retry_count = 0
        
        while retry_count < max_retries:
            # 检查任务状态
            status_info = self.get_task_status(task_id)
            status = status_info.get("status", "unknown")
            
            if status in ["completed", "failed"]:
                # 获取最终结果
                results = self.get_task_results(task_id)
                
                with self.results_lock:
                    self.results.append({
                        "url": url,
                        "task_id": task_id,
                        "status": status,
                        "results": results,
                        "timestamp": time.time()
                    })
                
                # 标记任务完成
                self.completed_tasks.add(url)
                
                # 输出结果
                if status == "completed":
                    print(f"✅ 成功: {url} (任务ID: {task_id})")
                else:
                    print(f"❌ 失败: {url} (任务ID: {task_id}) - 状态: {status}")
                
                break
            elif status == "in_progress":
                print(f"⏳ 处理中: {url} (任务ID: {task_id})")
            else:
                print(f"🔄 等待中: {url} (任务ID: {task_id}) - 状态: {status}")
            
            # 等待一段时间后重试
            time.sleep(5)
            retry_count += 1
        
        if retry_count >= max_retries:
            print(f"⏰ 超时: {url} (任务ID: {task_id})")
            with self.results_lock:
                self.results.append({
                    "url": url,
                    "task_id": task_id,
                    "status": "timeout",
                    "results": {"error": "轮询超时"},
                    "timestamp": time.time()
                })
            self.completed_tasks.add(url)
    
    def worker(self):
        """工作线程函数"""
        while True:
            url, task_id = self.task_queue.get()
            if url is None:  # 退出信号
                self.task_queue.task_done()
                break
            
            self.process_single_url(url, task_id)
            self.task_queue.task_done()
    
    def process_urls_from_file(self, filename: str, num_threads: int = 3):
        """从文件读取URL并处理"""
        # 读取URL文件
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"错误: 文件 '{filename}' 不存在")
            return
        except Exception as e:
            print(f"读取文件错误: {e}")
            return
        
        if not urls:
            print("错误: 文件中没有有效的URL")
            return
        
        print(f"📖 从文件读取到 {len(urls)} 个URL")
        
        # 检查服务器健康状态
        print("🔍 检查服务器状态...")
        if not self.check_health():
            print("❌ 服务器不可用，请确保服务已启动")
            return
        print("✅ 服务器连接正常")
        
        # 启动工作线程
        print(f"🚀 启动 {num_threads} 个工作线程...")
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=self.worker)
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # 分批提交URL（避免一次性提交太多）
        batch_size = 10
        total_submitted = 0
        
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i:i + batch_size]
            print(f"📤 提交批次 {i//batch_size + 1}: {len(batch_urls)} 个URL")
            
            # 提交任务
            task_id = self.submit_scraping_task(batch_urls)
            if task_id:
                # 将批次中的每个URL和任务ID加入队列
                for url in batch_urls:
                    self.task_queue.put((url, task_id))
                    total_submitted += 1
            else:
                print(f"❌ 批次 {i//batch_size + 1} 提交失败")
            
            # 批次间延迟，避免服务器压力过大
            time.sleep(2)
        
        print(f"✅ 已提交 {total_submitted} 个URL到处理队列")
        
        # 等待所有任务完成
        self.task_queue.join()
        
        # 发送退出信号给工作线程
        for _ in range(num_threads):
            self.task_queue.put((None, None))
        
        # 等待所有线程结束
        for thread in threads:
            thread.join()
        
        print("🎉 所有URL处理完成!")
        
        # 保存结果
        self.save_results()
    
    def save_results(self):
        """保存结果到文件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_files = []
        
        # 保存详细结果（JSON格式）
        detailed_filename = f"scraping_results_{timestamp}.json"
        with open(detailed_filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        output_files.append(detailed_filename)
        
        # 保存摘要结果（文本格式）
        summary_filename = f"scraping_summary_{timestamp}.txt"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write(f"URL爬取结果摘要 - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            success_count = sum(1 for r in self.results if r['status'] == 'completed')
            failed_count = sum(1 for r in self.results if r['status'] in ['failed', 'timeout'])
            
            f.write(f"总计URL数量: {len(self.results)}\n")
            f.write(f"成功数量: {success_count}\n")
            f.write(f"失败数量: {failed_count}\n")
            f.write(f"成功率: {success_count/len(self.results)*100:.1f}%\n\n")
            
            f.write("成功URL列表:\n")
            for result in self.results:
                if result['status'] == 'completed':
                    f.write(f"✅ {result['url']}\n")
            
            f.write("\n失败URL列表:\n")
            for result in self.results:
                if result['status'] in ['failed', 'timeout']:
                    f.write(f"❌ {result['url']} ({result['status']})\n")
        
        output_files.append(summary_filename)
        
        # 保存成功URL列表（纯文本）
        success_urls_filename = f"success_urls_{timestamp}.txt"
        with open(success_urls_filename, 'w', encoding='utf-8') as f:
            for result in self.results:
                if result['status'] == 'completed':
                    f.write(result['url'] + "\n")
        output_files.append(success_urls_filename)
        
        print(f"💾 结果已保存到以下文件:")
        for filename in output_files:
            print(f"   - {filename}")

def main():
    parser = argparse.ArgumentParser(description='批量URL爬取工具')
    parser.add_argument('input_file', help='包含URL的输入文件（每行一个URL）')
    parser.add_argument('--api-url', default='http://localhost:5000', 
                       help='API服务器地址 (默认: http://localhost:5000)')
    parser.add_argument('--api-key', default='demo-api-key-123', 
                       help='API密钥 (默认: demo-api-key-123)')
    parser.add_argument('--threads', type=int, default=3, 
                       help='工作线程数量 (默认: 3)')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_file):
        print(f"错误: 文件 '{args.input_file}' 不存在")
        return
    
    # 创建爬取器实例
    scraper = URLScraper(api_url=args.api_url, api_key=args.api_key)
    
    # 开始处理
    try:
        scraper.process_urls_from_file(args.input_file, args.threads)
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断操作")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()