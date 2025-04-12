#!/usr/bin/env python
"""
测试XMind生成器对大量节点的支持
生成一个具有5000+节点的XMind文件用于测试
"""

import os
import sys
import logging
import random
import time
from datetime import datetime

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_large_mindmap")

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.parser import parse_text
from src.xmind_generator import create_xmind_from_structure

def generate_large_text_structure(num_main_topics=10, topics_per_level=10, max_depth=3):
    """
    生成大型文本结构用于测试
    
    Args:
        num_main_topics (int): 主题数量
        topics_per_level (int): 每个主题的子主题数量
        max_depth (int): 最大深度
        
    Returns:
        str: 生成的文本
    """
    logger.info(f"生成大型文本结构: {num_main_topics}个主题, 每级{topics_per_level}个子主题, 最大深度{max_depth}")
    
    # 估算节点总数
    total_nodes = 1  # 根节点
    for depth in range(1, max_depth + 1):
        total_nodes += num_main_topics * (topics_per_level ** (depth - 1))
    
    logger.info(f"预计总节点数: {total_nodes}")
    
    # 生成根主题
    root_title = f"大型思维导图测试 ({total_nodes}个节点)"
    text = [root_title]
    
    # 生成一些随机主题内容
    topics = [
        "项目管理", "软件开发", "数据分析", "人工智能", "机器学习", 
        "深度学习", "计算机视觉", "自然语言处理", "数据库", "网络安全",
        "Web开发", "移动开发", "云计算", "大数据", "区块链",
        "IoT物联网", "DevOps", "敏捷开发", "测试", "用户体验"
    ]
    
    # 生成主题
    def generate_topics(depth, parent_indent):
        if depth > max_depth:
            return
        
        # 确定当前级别的主题数量
        if depth == 1:
            current_topics = num_main_topics
        else:
            current_topics = topics_per_level
        
        # 生成当前级别的主题
        for i in range(current_topics):
            topic = random.choice(topics) + f" {depth}.{i+1}"
            text.append(parent_indent + "    " + topic)
            generate_topics(depth + 1, parent_indent + "    ")
    
    # 从第一级开始生成主题
    generate_topics(1, "")
    
    # 转换为文本
    return "\n".join(text)

def test_large_mindmap():
    """测试生成大型思维导图"""
    # 开始计时
    start_time = time.time()
    
    # 设置输出文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文本结构
    text = generate_large_text_structure(15, 10, 3)  # 应该生成约1500个节点
    
    # 将文本保存到文件
    text_file = os.path.join(output_dir, f"large_mindmap_{timestamp}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"已保存文本文件: {text_file}")
    
    # 解析文本
    logger.info("开始解析文本...")
    structure = parse_text(text)
    
    # 生成XMind文件
    xmind_file = os.path.join(output_dir, f"large_mindmap_{timestamp}.xmind")
    logger.info(f"开始生成XMind文件: {xmind_file}")
    create_xmind_from_structure(structure, xmind_file)
    
    # 输出文件大小
    file_size = os.path.getsize(xmind_file)
    logger.info(f"XMind文件生成完成: {xmind_file}, 大小: {file_size/1024:.2f} KB")
    
    # 结束计时
    elapsed_time = time.time() - start_time
    logger.info(f"总耗时: {elapsed_time:.2f} 秒")
    
    return xmind_file

def test_very_large_mindmap():
    """测试生成超大型思维导图 (5000+节点)"""
    # 开始计时
    start_time = time.time()
    
    # 设置输出文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成文本结构 - 超过5000个节点
    text = generate_large_text_structure(20, 8, 4)  # 应该生成约5000个节点
    
    # 将文本保存到文件
    text_file = os.path.join(output_dir, f"very_large_mindmap_{timestamp}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)
    logger.info(f"已保存文本文件: {text_file}")
    
    # 解析文本
    logger.info("开始解析文本...")
    structure = parse_text(text)
    
    # 生成XMind文件
    xmind_file = os.path.join(output_dir, f"very_large_mindmap_{timestamp}.xmind")
    logger.info(f"开始生成XMind文件: {xmind_file}")
    create_xmind_from_structure(structure, xmind_file)
    
    # 输出文件大小
    file_size = os.path.getsize(xmind_file)
    logger.info(f"XMind文件生成完成: {xmind_file}, 大小: {file_size/1024:.2f} KB")
    
    # 结束计时
    elapsed_time = time.time() - start_time
    logger.info(f"总耗时: {elapsed_time:.2f} 秒")
    
    return xmind_file

if __name__ == "__main__":
    logger.info("开始测试...")
    
    # 普通大型思维导图测试
    xmind_file = test_large_mindmap()
    
    # 输出结果
    logger.info(f"测试完成。生成的XMind文件: {xmind_file}")
    logger.info("请用XMind打开此文件，检查是否所有内容都可见")
    
    # 询问是否继续测试超大型思维导图
    response = input("是否继续测试超大型思维导图 (5000+节点)? (y/n): ")
    if response.lower() == 'y':
        xmind_file = test_very_large_mindmap()
        logger.info(f"超大型测试完成。生成的XMind文件: {xmind_file}")
        logger.info("请用XMind打开此文件，检查是否所有内容都可见")
    
    logger.info("所有测试完成。") 