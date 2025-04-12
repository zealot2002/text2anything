"""
Text parser for converting indented text to a hierarchical structure.
"""
import logging
import os

# 配置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), "parser_debug.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("text_parser")

def count_leading_spaces(line):
    """Count the number of leading spaces in a line."""
    return len(line) - len(line.lstrip())

def parse_text(text):
    """
    Parse indented text into a hierarchical structure.
    
    Args:
        text (str): The input text with indentation representing hierarchy.
        
    Returns:
        dict: A dictionary representing the hierarchical structure.
    """
    logger.info(f"开始解析文本，长度: {len(text)} 字符")
    
    lines = text.strip().split("\n")
    logger.info(f"文本被分割为 {len(lines)} 行")
    
    if not lines or not text.strip():
        logger.warning("输入为空，返回默认结构")
        return {"title": "Empty", "topics": []}
    
    # Handle the case when the first line has a dash/bullet
    first_line = lines[0].strip()
    if first_line.startswith('-'):
        first_line = first_line[1:].strip()
        logger.debug(f"根主题（去除破折号）: {first_line}")
    else:
        logger.debug(f"根主题: {first_line}")
    
    # First line is the root topic
    root = {"title": first_line, "topics": []}
    
    # Stack to keep track of the current path in the hierarchy
    stack = [(0, root)]  # (indentation_level, node)
    
    logger.info("开始处理每一行...")
    for i in range(1, len(lines)):
        line = lines[i]
        if not line.strip():  # Skip empty lines
            logger.debug(f"跳过空行 #{i+1}")
            continue
            
        current_indent = count_leading_spaces(line)
        title = line.strip()
        
        # Remove leading dash/bullet if present
        if title.startswith('-'):
            title = title[1:].strip()
            
        logger.debug(f"行 #{i+1}: 缩进={current_indent}, 标题='{title}'")
        
        # Create new node
        new_node = {"title": title, "topics": []}
        
        # Find the parent for this node
        while stack and stack[-1][0] >= current_indent:
            popped = stack.pop()
            logger.debug(f"从栈中弹出缩进级别 {popped[0]}")
        
        if not stack:  # This should not happen with well-formed input
            logger.warning("栈为空，这不应该发生！将节点添加到根节点下")
            stack.append((0, root))
            
        # Add new node to its parent
        parent_node = stack[-1][1]
        parent_title = parent_node.get("title", "无标题")
        logger.debug(f"将节点 '{title}' 添加到父节点 '{parent_title}' 下")
        parent_node["topics"].append(new_node)
        
        # Add new node to stack
        stack.append((current_indent, new_node))
    
    logger.info(f"解析完成，生成的结构包含 {len(root['topics'])} 个顶级主题")
    
    # 记录整个结构的完整信息
    log_structure_info(root)
    
    return root

def log_structure_info(node, level=0, path="根节点"):
    """记录结构的详细信息"""
    logger.debug(f"{'  ' * level}路径: {path}, 标题: {node['title']}, 子主题数: {len(node.get('topics', []))}")
    for i, topic in enumerate(node.get("topics", [])):
        log_structure_info(topic, level+1, f"{path} > {i+1}")

if __name__ == "__main__":
    # Simple test
    test_text = """- Root Topic
    - Subtopic 1
        - Sub-subtopic A
        - Sub-subtopic B
    - Subtopic 2
        - Sub-subtopic C"""
    
    result = parse_text(test_text)
    print(result) 