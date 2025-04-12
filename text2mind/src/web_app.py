"""
Web interface for the text2mind tool.
"""

import os
import tempfile
import uuid
import sys
import logging
from flask import Flask, request, render_template, send_file, url_for, Response

# 配置详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webapp_debug.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web_app")

# Allow relative imports when running as script
if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use relative imports for package
try:
    from .parser import parse_text
    from .xmind_generator import create_xmind_from_structure
except ImportError:
    # When run directly
    from parser import parse_text
    from xmind_generator import create_xmind_from_structure

# Define template directory
template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
app = Flask(__name__, template_folder=template_dir)

# 增加上传文件大小限制
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Create a directory for temporary files
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'text2mind')
os.makedirs(TEMP_DIR, exist_ok=True)

@app.route('/')
def index():
    """Render the main page."""
    logger.info("访问首页")
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    """Convert text to mind map xmind file."""
    logger.info("收到转换请求")
    
    text = request.form.get('text', '')
    logger.info(f"收到文本，长度: {len(text)}")
    
    if not text:
        logger.warning("未提供文本内容")
        return render_template('index.html', error='Please enter some text.')
    
    # 保存原始文本以便调试
    text_id = str(uuid.uuid4())
    original_text_path = os.path.join(TEMP_DIR, f"{text_id}.txt")
    try:
        with open(original_text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logger.debug(f"原始文本已保存到: {original_text_path}")
    except Exception as e:
        logger.error(f"保存原始文本时出错: {e}", exc_info=True)
    
    # Generate unique filenames
    xmind_path = os.path.join(TEMP_DIR, f"{text_id}.xmind")
    
    try:
        # Parse the text
        logger.info("开始解析文本...")
        structure = parse_text(text)
        logger.info(f"解析完成，生成结构中顶级主题数: {len(structure.get('topics', []))}")
        
        # 保存解析后的结构以便调试
        try:
            import json
            structure_path = os.path.join(TEMP_DIR, f"{text_id}.json")
            with open(structure_path, 'w', encoding='utf-8') as f:
                json.dump(structure, f, ensure_ascii=False, indent=2)
            logger.debug(f"解析后的结构已保存到: {structure_path}")
        except Exception as e:
            logger.error(f"保存结构时出错: {e}", exc_info=True)
        
        # Create XMind file
        logger.info("开始创建XMind文件...")
        create_xmind_from_structure(structure, xmind_path)
        logger.info(f"XMind文件创建完成: {xmind_path}")
        
        # 查看并记录生成的文件大小
        file_size = os.path.getsize(xmind_path)
        logger.info(f"生成的XMind文件大小: {file_size} 字节")
        
        # Return the XMind file
        return send_file(xmind_path, 
                         mimetype='application/octet-stream',
                         as_attachment=True, 
                         download_name='mindmap.xmind')
    except Exception as e:
        logger.error(f"处理请求时出错: {e}", exc_info=True)
        return render_template('index.html', error=f'An error occurred: {str(e)}')

# 添加一个简单的健康检查路由
@app.route('/health')
def health():
    logger.info("健康检查请求")
    return Response('OK', status=200)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs(template_dir, exist_ok=True)
    
    # Create a simple HTML template
    with open(os.path.join(template_dir, 'index.html'), 'w') as f:
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
    <p>Convert indented text to a mind map XMind file.</p>
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
        <button type="submit">Download XMind File</button>
    </form>
    <p><small>Note: The generated mind map will use special layout settings to ensure all content is displayed.</small></p>
</body>
</html>""")
    
    logger.info("Web服务启动中，监听端口: 8088")
    app.run(debug=True, host='0.0.0.0', port=8088) 