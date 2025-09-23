#!/usr/bin/env python3
"""
文件处理工具
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any

def save_json_data(data: Dict[str, Any], output_path: Path) -> bool:
    """保存JSON数据到文件"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON数据失败 {output_path}: {e}")
        return False

def load_json_data(input_path: Path) -> Dict[str, Any]:
    """从文件加载JSON数据"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON数据失败 {input_path}: {e}")
        return {}

def generate_filename_from_url(url: str) -> str:
    """从URL生成文件名（使用MD5哈希）"""
    # 使用MD5哈希生成文件名，避免URL中的特殊字符问题
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return f"{url_hash}.json"

def url_to_filename(url: str) -> str:
    """将URL转换为文件名（兼容旧版本）"""
    # 兼容旧版本的URL转文件名方法
    return (url.replace('://', '_')
               .replace('/', '_')
               .replace('?', '_')
               .replace('=', '_')
               .replace('&', '_') + '.json')