#!/usr/bin/env python

import json
from src.parser import parse_text

# 读取示例文件
with open('examples/example.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 解析内容
result = parse_text(content)

# 输出解析结果
print(json.dumps(result, ensure_ascii=False, indent=2))

# 检查是否存在"下周工作计划"节点
found_next_week = False

def check_next_week(node, level=0):
    global found_next_week
    indent = "  " * level
    title = node["title"]
    print(f"{indent}- {title}")
    
    if title == "下周工作计划":
        found_next_week = True
        print(f"{indent}  找到了下周工作计划节点！")
    
    for topic in node.get("topics", []):
        check_next_week(topic, level + 1)

print("\n解析树结构:")
check_next_week(result)

if not found_next_week:
    print("\n警告: 没有找到'下周工作计划'节点")

# 检查输入文本
print("\n输入文本结构分析:")
lines = content.split("\n")
for i, line in enumerate(lines):
    if "下周工作计划" in line:
        print(f"行 {i+1}: {line}")
        prev_line = lines[i-1] if i > 0 else "无"
        next_line = lines[i+1] if i < len(lines)-1 else "无"
        print(f"上一行: {prev_line}")
        print(f"下一行: {next_line}")
        print(f"缩进空格数: {len(line) - len(line.lstrip())}")
        
        # 查看周围的一些行
        start = max(0, i-3)
        end = min(len(lines), i+4)
        print("\n上下文:")
        for j in range(start, end):
            if j == i:
                print(f"{j+1}: >>> {lines[j]}")
            else:
                print(f"{j+1}: {lines[j]}") 