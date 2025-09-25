import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from typing import Dict, List
import json
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class BaseSimpleScraper:
    """基础简单爬虫"""
    
    def __init__(self, name):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        # 异步会话缓存
        self._async_session = None
    
    async def _get_async_session(self):
        """获取或创建异步会话"""
        if self._async_session is None or self._async_session.closed:
            self._async_session = aiohttp.ClientSession(
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                },
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._async_session
    
    async def close_async_session(self):
        """关闭异步会话"""
        if self._async_session and not self._async_session.closed:
            await self._async_session.close()
    
    def scrape_url(self, url: str) -> Dict:
        """基础爬取方法，子类可以重写"""
        try:
            logger.info(f"[{self.name}] 开始爬取: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取标题
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "无标题"
            
            # 提取正文内容
            for script in soup(["script", "style"]):
                script.decompose()
            
            content = soup.get_text()
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
                'error': None,
                'scraper_type': self.name
            }
            
            logger.info(f"[{self.name}] 爬取成功: {url}, 标题: {title_text}")
            return result
            
        except Exception as e:
            logger.error(f"[{self.name}] 爬取失败: {url} - {str(e)}")
            return {
                'url': url,
                'success': False,
                'title': None,
                'content': None,
                'publish_date': None,
                'error': str(e),
                'scraper_type': self.name
            }
    
    async def scrape_url_async(self, url: str) -> Dict:
        """异步版本的基础爬取方法"""
        try:
            logger.info(f"[{self.name}] 异步爬取: {url}")
            
            session = await self._get_async_session()
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                # 解析HTML
                soup = BeautifulSoup(content, 'html.parser')
                
                # 提取标题
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "无标题"
                
                # 提取正文内容
                for script in soup(["script", "style"]):
                    script.decompose()
                
                content = soup.get_text()
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
                    'error': None,
                    'scraper_type': self.name
                }
                
                logger.info(f"[{self.name}] 异步爬取成功: {url}, 标题: {title_text}")
                return result
            
        except Exception as e:
            logger.error(f"[{self.name}] 异步爬取失败: {url} - {str(e)}")
            return {
                'url': url,
                'success': False,
                'title': None,
                'content': None,
                'publish_date': None,
                'error': str(e),
                'scraper_type': self.name
            }

class SimpleNewspaperScraper(BaseSimpleScraper):
    """Newspaper3k 简单实现"""
    
    def __init__(self):
        super().__init__("newspaper")
    
    def scrape_url(self, url: str) -> Dict:
        """使用newspaper3k逻辑"""
        try:
            logger.info(f"[newspaper] 开始爬取: {url}")
            
            # 模拟newspaper3k的提取逻辑
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 更智能的标题提取
            title = None
            for selector in ['h1', 'title', '.title', '#title', 'h2']:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text().strip()
                    break
            
            if not title:
                title = "无标题"
            
            # 更智能的内容提取
            content = ""
            for selector in ['article', 'main', '.content', '#content', '.post', '.article']:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text().strip()
                    break
            
            if not content:
                content = soup.get_text().strip()
            
            # 清理和限制长度
            if len(content) > 5000:
                content = content[:5000] + "..."
            
            result = {
                'url': url,
                'success': True,
                'title': title,
                'content': content,
                'publish_date': None,
                'error': None,
                'scraper_type': self.name
            }
            
            logger.info(f"[newspaper] 爬取成功: {url}, 标题: {title}")
            return result
            
        except Exception as e:
            logger.error(f"[newspaper] 爬取失败: {url} - {str(e)}")
            return super().scrape_url(url)  # 回退到基础方法
    
    async def scrape_url_async(self, url: str) -> Dict:
        """异步版本的newspaper爬取方法"""
        try:
            logger.info(f"[newspaper] 异步爬取: {url}")
            
            session = await self._get_async_session()
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # 更智能的标题提取
                title = None
                for selector in ['h1', 'title', '.title', '#title', 'h2']:
                    element = soup.select_one(selector)
                    if element:
                        title = element.get_text().strip()
                        break
                
                if not title:
                    title = "无标题"
                
                # 更智能的内容提取
                content = ""
                for selector in ['article', 'main', '.content', '#content', '.post', '.article']:
                    element = soup.select_one(selector)
                    if element:
                        content = element.get_text().strip()
                        break
                
                if not content:
                    content = soup.get_text().strip()
                
                # 清理和限制长度
                if len(content) > 5000:
                    content = content[:5000] + "..."
                
                result = {
                    'url': url,
                    'success': True,
                    'title': title,
                    'content': content,
                    'publish_date': None,
                    'error': None,
                    'scraper_type': self.name
                }
                
                logger.info(f"[newspaper] 异步爬取成功: {url}, 标题: {title}")
                return result
                
        except Exception as e:
            logger.error(f"[newspaper] 异步爬取失败: {url} - {str(e)}")
            return await super().scrape_url_async(url)  # 回退到基础异步方法

class SimpleReadabilityScraper(BaseSimpleScraper):
    """Readability 简单实现"""
    
    def __init__(self):
        super().__init__("readability")
    
    def scrape_url(self, url: str) -> Dict:
        """使用readability逻辑"""
        try:
            logger.info(f"[readability] 开始爬取: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除不需要的元素
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # 寻找主要内容区域
            content_area = None
            for selector in ['article', 'main', '.article', '.post', '.content', '#content']:
                content_area = soup.select_one(selector)
                if content_area:
                    break
            
            if not content_area:
                content_area = soup.find('body')
            
            # 提取标题
            title = None
            for selector in ['h1', 'title']:
                element = content_area.select_one(selector) if content_area else soup.select_one(selector)
                if element:
                    title = element.get_text().strip()
                    break
            
            if not title:
                title = "无标题"
            
            # 提取内容
            content = content_area.get_text() if content_area else soup.get_text()
            content = ' '.join(content.split())  # 清理空白字符
            
            if len(content) > 5000:
                content = content[:5000] + "..."
            
            result = {
                'url': url,
                'success': True,
                'title': title,
                'content': content,
                'publish_date': None,
                'error': None,
                'scraper_type': self.name
            }
            
            logger.info(f"[readability] 爬取成功: {url}, 标题: {title}")
            return result
            
        except Exception as e:
            logger.error(f"[readability] 爬取失败: {url} - {str(e)}")
            return super().scrape_url(url)
    
    async def scrape_url_async(self, url: str) -> Dict:
        """异步版本的readability爬取方法"""
        try:
            logger.info(f"[readability] 异步爬取: {url}")
            
            session = await self._get_async_session()
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # 移除不需要的元素
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # 寻找主要内容区域
                content_area = None
                for selector in ['article', 'main', '.article', '.post', '.content', '#content']:
                    content_area = soup.select_one(selector)
                    if content_area:
                        break
                
                if not content_area:
                    content_area = soup.find('body')
                
                # 提取标题
                title = None
                for selector in ['h1', 'title']:
                    element = content_area.select_one(selector) if content_area else soup.select_one(selector)
                    if element:
                        title = element.get_text().strip()
                        break
                
                if not title:
                    title = "无标题"
                
                # 提取内容
                content = content_area.get_text() if content_area else soup.get_text()
                content = ' '.join(content.split())  # 清理空白字符
                
                if len(content) > 5000:
                    content = content[:5000] + "..."
                
                result = {
                    'url': url,
                    'success': True,
                    'title': title,
                    'content': content,
                    'publish_date': None,
                    'error': None,
                    'scraper_type': self.name
                }
                
                logger.info(f"[readability] 异步爬取成功: {url}, 标题: {title}")
                return result
                
        except Exception as e:
            logger.error(f"[readability] 异步爬取失败: {url} - {str(e)}")
            return await super().scrape_url_async(url)

class SimpleTrafilaturaScraper(BaseSimpleScraper):
    """Trafilatura 简单实现"""
    
    def __init__(self):
        super().__init__("trafilatura")
    
    def scrape_url(self, url: str) -> Dict:
        """使用trafilatura逻辑"""
        try:
            logger.info(f"[trafilatura] 开始爬取: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取结构化数据
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "无标题"
            
            # 寻找主要内容
            main_content = ""
            
            # 尝试不同的内容选择器
            content_selectors = [
                'article', 'main', '.article', '.post', '.content',
                '#content', '.entry', '.post-content', '.article-content'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    main_content = ' '.join(elem.get_text() for elem in elements)
                    break
            
            if not main_content:
                # 回退到body内容，但排除导航和侧边栏
                body = soup.find('body')
                if body:
                    # 移除导航和侧边栏
                    for nav in body.select('nav, .nav, .navigation, .menu, .sidebar'):
                        nav.decompose()
                    main_content = body.get_text()
            
            # 清理内容
            main_content = ' '.join(main_content.split())
            if len(main_content) > 5000:
                main_content = main_content[:5000] + "..."
            
            result = {
                'url': url,
                'success': True,
                'title': title_text,
                'content': main_content,
                'publish_date': None,
                'error': None,
                'scraper_type': self.name
            }
            
            logger.info(f"[trafilatura] 爬取成功: {url}, 标题: {title_text}")
            return result
            
        except Exception as e:
            logger.error(f"[trafilatura] 爬取失败: {url} - {str(e)}")
            return super().scrape_url(url)
    
    async def scrape_url_async(self, url: str) -> Dict:
        """异步版本的trafilatura爬取方法"""
        try:
            logger.info(f"[trafilatura] 异步爬取: {url}")
            
            session = await self._get_async_session()
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                
                soup = BeautifulSoup(content, 'html.parser')
                
                # 提取结构化数据
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "无标题"
                
                # 寻找主要内容
                main_content = ""
                
                # 尝试不同的内容选择器
                content_selectors = [
                    'article', 'main', '.article', '.post', '.content',
                    '#content', '.entry', '.post-content', '.article-content'
                ]
                
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        main_content = ' '.join(elem.get_text() for elem in elements)
                        break
                
                if not main_content:
                    # 回退到body内容，但排除导航和侧边栏
                    body = soup.find('body')
                    if body:
                        # 移除导航和侧边栏
                        for nav in body.select('nav, .nav, .navigation, .menu, .sidebar'):
                            nav.decompose()
                        main_content = body.get_text()
                
                # 清理内容
                main_content = ' '.join(main_content.split())
                if len(main_content) > 5000:
                    main_content = main_content[:5000] + "..."
                
                result = {
                    'url': url,
                    'success': True,
                    'title': title_text,
                    'content': main_content,
                    'publish_date': None,
                    'error': None,
                    'scraper_type': self.name
                }
                
                logger.info(f"[trafilatura] 异步爬取成功: {url}, 标题: {title_text}")
                return result
                
        except Exception as e:
            logger.error(f"[trafilatura] 异步爬取失败: {url} - {str(e)}")
            return await super().scrape_url_async(url)

# 爬虫映射
SCRAPERS = {
    'requests': BaseSimpleScraper('requests'),
    'newspaper': SimpleNewspaperScraper(),
    'readability': SimpleReadabilityScraper(),
    'trafilatura': SimpleTrafilaturaScraper(),
}

def scrape_with_scraper(url: str, scraper_type: str) -> Dict:
    """使用指定爬虫爬取URL"""
    if scraper_type not in SCRAPERS:
        raise ValueError(f"不支持的爬虫类型: {scraper_type}")
    
    scraper = SCRAPERS[scraper_type]
    return scraper.scrape_url(url)

async def scrape_with_scraper_async(url: str, scraper_type: str) -> Dict:
    """异步使用指定爬虫爬取URL"""
    if scraper_type not in SCRAPERS:
        raise ValueError(f"不支持的爬虫类型: {scraper_type}")
    
    scraper = SCRAPERS[scraper_type]
    return await scraper.scrape_url_async(url)

async def scrape_urls_async(urls: List[str], scraper_type: str) -> List[Dict]:
    """异步批量爬取URLs"""
    tasks = []
    for url in urls:
        task = scrape_with_scraper_async(url, scraper_type)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理异常结果
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"异步爬取异常: {urls[i]} - {str(result)}")
            processed_results.append({
                'url': urls[i],
                'success': False,
                'title': None,
                'content': None,
                'publish_date': None,
                'error': str(result),
                'scraper_type': scraper_type
            })
        else:
            processed_results.append(result)
    
    return processed_results

async def close_all_scraper_sessions():
    """关闭所有爬虫的异步会话"""
    for scraper in SCRAPERS.values():
        await scraper.close_async_session()

def scrape_with_all_scrapers(url: str) -> List[Dict]:
    """使用所有爬虫爬取URL（用于竞速模式）"""
    results = []
    for scraper_type in ['requests', 'newspaper', 'readability', 'trafilatura']:
        try:
            result = scrape_with_scraper(url, scraper_type)
            results.append(result)
        except Exception as e:
            logger.error(f"爬虫 {scraper_type} 失败: {e}")
            results.append({
                'url': url,
                'success': False,
                'error': str(e),
                'scraper_type': scraper_type
            })
    
    return results

async def main_async():
    """异步测试主函数"""
    test_urls = ["https://example.com", "https://httpbin.org/html"]
    
    print("=== 异步批量爬取测试 ===")
    results = await scrape_urls_async(test_urls, 'requests')
    
    for result in results:
        print(f"\n{result['scraper_type']}: {'✅ 成功' if result['success'] else '❌ 失败'}")
        if result['success']:
            print(f"  URL: {result['url']}")
            print(f"  标题: {result['title']}")
            print(f"  内容长度: {len(result['content'])} 字符")
        else:
            print(f"  错误: {result['error']}")
    
    # 关闭所有异步会话
    await close_all_scraper_sessions()

if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(main_async())