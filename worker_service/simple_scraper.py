import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class SimpleRequestsScraper:
    """简单的requests爬虫实现"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def scrape_url(self, url: str) -> Dict:
        """爬取单个URL"""
        try:
            logger.info(f"开始爬取: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "无标题"
            
            # 提取正文内容
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取正文
            content = soup.get_text()
            
            # 清理空白字符
            lines = (line.strip() for line in content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)
            
            # 限制内容长度
            if len(content) > 5000:
                content = content[:5000] + "..."
            
            result = {
                'url': url,
                'success': True,
                'title': title_text,
                'content': content,
                'publish_date': None,
                'error': None
            }
            
            logger.info(f"爬取成功: {url}, 标题: {title_text}")
            return result
            
        except Exception as e:
            logger.error(f"爬取失败: {url} - {str(e)}")
            return {
                'url': url,
                'success': False,
                'title': None,
                'content': None,
                'publish_date': None,
                'error': str(e)
            }

def scrape_urls(urls: List[str]) -> List[Dict]:
    """批量爬取URLs"""
    scraper = SimpleRequestsScraper()
    results = []
    
    for i, url in enumerate(urls):
        try:
            logger.info(f"爬取进度: {i+1}/{len(urls)} - {url}")
            result = scraper.scrape_url(url)
            results.append(result)
        except Exception as e:
            logger.error(f"爬取异常: {url} - {str(e)}")
            results.append({
                'url': url,
                'success': False,
                'title': None,
                'content': None,
                'publish_date': None,
                'error': str(e)
            })
    
    return results

if __name__ == "__main__":
    # 测试
    test_urls = ["https://example.com", "https://httpbin.org/html"]
    results = scrape_urls(test_urls)
    
    for result in results:
        print(f"URL: {result['url']}")
        print(f"成功: {result['success']}")
        if result['success']:
            print(f"标题: {result['title']}")
            print(f"内容长度: {len(result['content'])} 字符")
        else:
            print(f"错误: {result['error']}")
        print("-" * 50)