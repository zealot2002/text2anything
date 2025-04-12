#!/usr/bin/env python
"""
Script to run the text2mind web interface.
"""

import os
import sys
import logging
import time
from datetime import datetime

# 配置详细的日志记录
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"text2mind_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run_web_app")

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Ensure template directory exists
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(template_dir, exist_ok=True)

# Ensure the template file exists
template_file = os.path.join(template_dir, 'index.html')
if not os.path.exists(template_file):
    logger.info(f"创建模板文件: {template_file}")
    with open(template_file, 'w') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Text2Mind</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        textarea {
            width: 100%;
            height: 500px;
            margin-bottom: 10px;
            font-family: monospace;
        }
        .error {
            color: red;
        }
    </style>
</head>
<body>
    <h1>Text2Mind</h1>
    <p>Convert indented text to a mind map.</p>
    <p>Use 4 spaces to indicate levels in the hierarchy. The tool will automatically convert your text to a mind map.</p>
    
    {% if error %}
    <p class="error">{{ error }}</p>
    {% endif %}
    
    <form action="/convert" method="post">
        <textarea name="text" placeholder="Enter your indented text here...">Python Programming
    Core Concepts
        Variables
        Data Types
    Advanced Topics
        Object-Oriented Programming
            Classes
            Inheritance</textarea>
        <br>
        <button type="submit">Generate Mind Map</button>
    </form>
    <p><small>Note: The generated mind map will use special layout settings to ensure all content is displayed.</small></p>
</body>
</html>""")

from src.web_app import app

# 检查临时目录
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)
logger.info(f"临时目录已创建: {TEMP_DIR}")

def check_port_availability(port):
    """检查端口是否可用"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = True
    try:
        sock.bind(('0.0.0.0', port))
    except:
        result = False
    finally:
        sock.close()
    return result

if __name__ == '__main__':
    port = 8088
    MAX_RETRIES = 5
    
    logger.info("启动text2mind web服务...")
    
    # 检查端口是否可用，尝试多次
    for attempt in range(MAX_RETRIES):
        if check_port_availability(port):
            logger.info(f"端口 {port} 可用，启动服务")
            break
        else:
            logger.warning(f"端口 {port} 已被占用，等待5秒后重试...")
            time.sleep(5)
            if attempt == MAX_RETRIES - 1:
                # 尝试使用不同的端口
                for alt_port in range(8089, 8100):
                    if check_port_availability(alt_port):
                        port = alt_port
                        logger.info(f"切换到备用端口 {port}")
                        break
    
    try:
        logger.info(f"启动Web服务，监听端口: {port}")
        app.run(debug=True, host='0.0.0.0', port=port) 
    except Exception as e:
        logger.error(f"启动服务时出错: {e}", exc_info=True) 