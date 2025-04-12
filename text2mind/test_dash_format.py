#!/usr/bin/env python

import sys
import json
from src.parser import parse_text

# 测试破折号格式的内容
test_text = """- 周报
    - 本周工作内容（2025-04-12）
        - 微信小程序
            - 云仓小程序
    - 下周工作计划
        - 产品需求
            - qic服务——对外功能需求梳理，任务拆分
"""

result = parse_text(test_text)
print(json.dumps(result, ensure_ascii=False, indent=2))

# 确认下周工作计划是否正确解析
topics = result["topics"]
all_titles = []

def collect_titles(node):
    """递归收集所有标题"""
    all_titles.append(node["title"])
    for topic in node.get("topics", []):
        collect_titles(topic)

# 收集所有标题
for topic in topics:
    collect_titles(topic)

# 检查关键标题是否存在
expected_titles = [
    "本周工作内容（2025-04-12）", 
    "微信小程序", 
    "云仓小程序", 
    "下周工作计划", 
    "产品需求", 
    "qic服务——对外功能需求梳理，任务拆分"
]

missing_titles = [title for title in expected_titles if title not in all_titles]
if missing_titles:
    print("\n缺失的标题:")
    for title in missing_titles:
        print(f" - {title}")
else:
    print("\n所有预期标题都已找到！解析器修复成功。") 